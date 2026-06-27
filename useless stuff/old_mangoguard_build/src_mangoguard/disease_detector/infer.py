"""Single-image inference for the Streamlit "upload a leaf" experience.

Spec section 4.5 Module 1: load a checkpoint, run forward pass, return
the predicted class with calibrated probabilities + a Grad-CAM overlay.

A confidence flag (``low_confidence`` when ``max_prob < 0.8``) lets the
Streamlit page show a "model not sure -- consult an extension officer"
message instead of pretending certainty.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torchvision import transforms

from .gradcam import generate_heatmap, overlay_heatmap_on_image
from .model import build_model

_IMAGE_SIZE = 224
_IMAGENET_MEAN = (0.485, 0.456, 0.406)
_IMAGENET_STD = (0.229, 0.224, 0.225)
_LOW_CONFIDENCE_THRESHOLD = 0.8

# Default Alphonso Visit-1 classes -- the dashboard inference target.
DEFAULT_CLASSES: tuple[str, ...] = (
    "anthracnose",
    "powdery_mildew",
    "hopper",
    "sooty_mould",
    "healthy",
)


@dataclass(frozen=True, slots=True)
class DiseasePrediction:
    """One image's prediction + visualisation."""

    class_name: str
    confidence: float
    class_probabilities: dict[str, float]
    heatmap_overlay: np.ndarray
    low_confidence: bool


def _eval_transform() -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize((_IMAGE_SIZE, _IMAGE_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(_IMAGENET_MEAN, _IMAGENET_STD),
        ]
    )


def _load_image_rgb(image_path: Path) -> tuple[Image.Image, np.ndarray]:
    """Load and return both the PIL image (for transform) and a resized RGB array
    for the heatmap overlay.
    """
    img = Image.open(image_path).convert("RGB")
    resized = img.resize((_IMAGE_SIZE, _IMAGE_SIZE))
    rgb = np.asarray(resized, dtype=np.uint8)
    return img, rgb


def _load_model(
    model_path: Path | None,
    *,
    classes: tuple[str, ...],
    device: torch.device,
) -> torch.nn.Module:
    """Build the architecture, optionally load weights, set eval mode."""
    model = build_model(n_classes=len(classes), freeze_backbone=False)
    if model_path is not None and Path(model_path).exists():
        state = torch.load(model_path, map_location=device, weights_only=True)
        model.load_state_dict(state)
    model.to(device)
    model.eval()
    return model


def predict_image(
    image_path: str | Path,
    *,
    model_path: str | Path | None = None,
    classes: tuple[str, ...] = DEFAULT_CLASSES,
    device: str = "cpu",
) -> DiseasePrediction:
    """Run a single image through the fine-tuned MobileNetV3 + Grad-CAM.

    Args:
        image_path: Path to the leaf / fruit photo (any PIL-readable format).
        model_path: Path to a saved ``state_dict`` checkpoint. When ``None``,
            uses a freshly initialised model (Grad-CAM still works for visual
            debugging; probabilities will be random until trained).
        classes: Ordered tuple of class names matching the trained head.
        device: ``"cpu"`` or ``"cuda"``.

    Returns:
        ``DiseasePrediction`` with class name, confidence, full
        probability distribution, Grad-CAM overlay (uint8 RGB), and a
        ``low_confidence`` flag.
    """
    image_path = Path(image_path)
    if not image_path.exists():
        msg = f"Image not found: {image_path}"
        raise FileNotFoundError(msg)
    dev = torch.device(device)
    model = _load_model(
        Path(model_path) if model_path is not None else None,
        classes=classes,
        device=dev,
    )

    pil_img, rgb = _load_image_rgb(image_path)
    transform = _eval_transform()
    tensor = transform(pil_img).to(dev)
    with torch.no_grad():
        logits = model(tensor.unsqueeze(0))
        probs = torch.softmax(logits, dim=1)[0].cpu().numpy()

    top_idx = int(probs.argmax())
    top_prob = float(probs[top_idx])

    # Grad-CAM heatmap targeted at the top class
    heatmap = generate_heatmap(model, tensor, target_class=top_idx)
    overlay = overlay_heatmap_on_image(rgb, heatmap)

    return DiseasePrediction(
        class_name=classes[top_idx],
        confidence=top_prob,
        class_probabilities={cls: float(p) for cls, p in zip(classes, probs, strict=True)},
        heatmap_overlay=overlay,
        low_confidence=top_prob < _LOW_CONFIDENCE_THRESHOLD,
    )
