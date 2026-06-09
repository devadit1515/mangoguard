"""Grad-CAM++ heatmap generator with hand-rolled fallback.

Primary path: ``pytorch-grad-cam`` library. Fallback: a minimal
``torch.autograd.grad``-based implementation against the last conv
block of MobileNetV3-Small. The fallback only implements Grad-CAM
(not Grad-CAM++), which is fine for the Streamlit "show me what the
model looked at" use case -- Grad-CAM++ only differs noticeably for
multi-instance heatmaps which we don't need for single-leaf imagery.
"""

from __future__ import annotations

import logging

import numpy as np
import torch
from torch import nn

logger = logging.getLogger(__name__)


def _last_conv_layer(model: nn.Module) -> nn.Module:
    """Walk the backbone and return the last ``nn.Conv2d`` -- where the
    Grad-CAM gradients are computed against.
    """
    last_conv: nn.Module | None = None
    for module in model.modules():
        if isinstance(module, nn.Conv2d):
            last_conv = module
    if last_conv is None:
        msg = "Could not find a Conv2d layer in the model -- Grad-CAM impossible."
        raise ValueError(msg)
    return last_conv


def _fallback_gradcam(
    model: nn.Module,
    image_tensor: torch.Tensor,
    target_class: int | None = None,
) -> np.ndarray:
    """Minimal hand-rolled Grad-CAM.

    Hooks the last conv layer's activations + gradients, computes the
    weighted channel sum, ReLUs, normalises to [0,1].
    """
    model.eval()
    activations: dict[str, torch.Tensor] = {}
    gradients: dict[str, torch.Tensor] = {}
    last_conv = _last_conv_layer(model)

    def fwd_hook(_module, _inp, output) -> None:
        activations["value"] = output.detach()

    def bwd_hook(_module, _grad_in, grad_out) -> None:
        gradients["value"] = grad_out[0].detach()

    fwd_handle = last_conv.register_forward_hook(fwd_hook)
    bwd_handle = last_conv.register_full_backward_hook(bwd_hook)
    try:
        if image_tensor.ndim == 3:
            image_tensor = image_tensor.unsqueeze(0)
        image_tensor = image_tensor.clone().requires_grad_(True)
        logits = model(image_tensor)
        if target_class is None:
            target_class = int(logits.argmax(dim=1).item())
        # Backprop w.r.t. the chosen class logit
        model.zero_grad()
        logits[0, target_class].backward()

        acts = activations["value"][0]  # (C, h, w)
        grads = gradients["value"][0]  # (C, h, w)
        weights = grads.mean(dim=(1, 2))  # (C,) channel importance
        cam = (weights[:, None, None] * acts).sum(dim=0)
        cam = torch.relu(cam)
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
        cam_np = cam.cpu().numpy().astype(np.float32)
    finally:
        fwd_handle.remove()
        bwd_handle.remove()

    # Resize to input HxW
    target_h, target_w = image_tensor.shape[-2], image_tensor.shape[-1]
    cam_resized = _bilinear_resize(cam_np, (target_h, target_w))
    return cam_resized


def _bilinear_resize(arr: np.ndarray, new_shape: tuple[int, int]) -> np.ndarray:
    """Pure-numpy bilinear resize to avoid the OpenCV dependency just for this."""
    h_in, w_in = arr.shape
    h_out, w_out = new_shape
    if (h_in, w_in) == (h_out, w_out):
        return arr
    y = np.linspace(0, h_in - 1, h_out)
    x = np.linspace(0, w_in - 1, w_out)
    y0 = np.floor(y).astype(int).clip(0, h_in - 1)
    y1 = np.minimum(y0 + 1, h_in - 1)
    x0 = np.floor(x).astype(int).clip(0, w_in - 1)
    x1 = np.minimum(x0 + 1, w_in - 1)
    wy = (y - y0)[:, None]
    wx = (x - x0)[None, :]
    top = arr[y0[:, None], x0[None, :]] * (1 - wx) + arr[y0[:, None], x1[None, :]] * wx
    bot = arr[y1[:, None], x0[None, :]] * (1 - wx) + arr[y1[:, None], x1[None, :]] * wx
    return (top * (1 - wy) + bot * wy).astype(np.float32)


def generate_heatmap(
    model: nn.Module,
    image_tensor: torch.Tensor,
    target_class: int | None = None,
) -> np.ndarray:
    """Generate a normalised [0,1] heatmap of shape (H, W).

    Tries pytorch-grad-cam first; on ImportError or unexpected failure,
    falls back to ``_fallback_gradcam``.
    """
    try:
        from pytorch_grad_cam import GradCAMPlusPlus  # type: ignore[import-untyped]
        from pytorch_grad_cam.utils.model_targets import (  # type: ignore[import-untyped]
            ClassifierOutputTarget,
        )

        cam = GradCAMPlusPlus(model=model, target_layers=[_last_conv_layer(model)])
        targets = [ClassifierOutputTarget(target_class)] if target_class is not None else None
        input_batch = image_tensor.unsqueeze(0) if image_tensor.ndim == 3 else image_tensor
        grayscale_cam = cam(input_tensor=input_batch, targets=targets)[0]
        return grayscale_cam.astype(np.float32)
    except ImportError:
        logger.info("pytorch-grad-cam not installed -- using hand-rolled fallback Grad-CAM.")
    except Exception as exc:  # noqa: BLE001 -- best-effort, broad on purpose
        logger.warning("pytorch-grad-cam failed (%s); falling back.", exc)
    return _fallback_gradcam(model, image_tensor, target_class)


def overlay_heatmap_on_image(
    image_rgb: np.ndarray,
    heatmap: np.ndarray,
    alpha: float = 0.4,
) -> np.ndarray:
    """Blend a [0,1] heatmap with an RGB image (uint8 in 0-255). Returns uint8."""
    if image_rgb.dtype != np.uint8:
        image_rgb = (image_rgb * 255).clip(0, 255).astype(np.uint8)
    # Simple red-on-blue colormap to avoid the matplotlib dependency at runtime.
    cmap = np.zeros((*heatmap.shape, 3), dtype=np.float32)
    cmap[..., 0] = heatmap  # red channel scales with heatmap
    cmap[..., 2] = 1.0 - heatmap  # blue channel inverts
    cmap = (cmap * 255).astype(np.uint8)
    blended = ((1 - alpha) * image_rgb + alpha * cmap).clip(0, 255).astype(np.uint8)
    return blended
