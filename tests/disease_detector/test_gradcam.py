"""Tests for the Grad-CAM heatmap generator + fallback path."""

from __future__ import annotations

import builtins

import numpy as np
import pytest
import torch

from mangoguard.disease_detector.gradcam import (
    generate_heatmap,
    overlay_heatmap_on_image,
)
from mangoguard.disease_detector.model import build_model

_INPUT_HW = 224
_N_CLASSES = 5


@pytest.fixture
def model():
    return build_model(n_classes=_N_CLASSES)


@pytest.fixture
def image_tensor():
    return torch.randn(3, _INPUT_HW, _INPUT_HW)


def test_heatmap_shape_matches_input_image(model, image_tensor):
    heatmap = generate_heatmap(model, image_tensor)
    assert heatmap.shape == (_INPUT_HW, _INPUT_HW)


def test_heatmap_values_in_0_1(model, image_tensor):
    heatmap = generate_heatmap(model, image_tensor)
    assert heatmap.min() >= 0.0
    assert heatmap.max() <= 1.0 + 1e-6


def test_heatmap_is_float32(model, image_tensor):
    heatmap = generate_heatmap(model, image_tensor)
    assert heatmap.dtype == np.float32


def test_target_class_kwarg_changes_heatmap(model, image_tensor):
    h0 = generate_heatmap(model, image_tensor, target_class=0)
    h1 = generate_heatmap(model, image_tensor, target_class=1)
    # Targeting different classes should generally produce different heatmaps
    # (unless the model is degenerate -- very unlikely on a fresh init).
    assert not np.allclose(h0, h1)


def test_fallback_used_when_library_unavailable(monkeypatch, model, image_tensor):
    """Monkeypatch __import__ so pytorch_grad_cam can't load -- fallback should kick in."""
    real_import = builtins.__import__

    def patched_import(name, *args, **kwargs):
        if name.startswith("pytorch_grad_cam"):
            raise ImportError("simulated missing pytorch_grad_cam")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", patched_import)
    heatmap = generate_heatmap(model, image_tensor)
    assert heatmap.shape == (_INPUT_HW, _INPUT_HW)
    assert np.all(heatmap >= 0.0)


def test_overlay_returns_uint8_rgb(model, image_tensor):
    heatmap = generate_heatmap(model, image_tensor)
    image_rgb = np.random.randint(0, 256, (_INPUT_HW, _INPUT_HW, 3), dtype=np.uint8)
    overlay = overlay_heatmap_on_image(image_rgb, heatmap)
    assert overlay.shape == (_INPUT_HW, _INPUT_HW, 3)
    assert overlay.dtype == np.uint8


def test_overlay_alpha_blending_visible(model, image_tensor):
    """With alpha=1.0 the overlay must be the colormap (no original image)."""
    heatmap = generate_heatmap(model, image_tensor)
    image_rgb = np.zeros((_INPUT_HW, _INPUT_HW, 3), dtype=np.uint8)
    overlay_full = overlay_heatmap_on_image(image_rgb, heatmap, alpha=1.0)
    overlay_none = overlay_heatmap_on_image(image_rgb, heatmap, alpha=0.0)
    assert not np.array_equal(overlay_full, overlay_none)


def test_heatmap_handles_batch_dim(model):
    """Passing a (1, 3, H, W) batch should also work."""
    image_batch = torch.randn(1, 3, _INPUT_HW, _INPUT_HW)
    heatmap = generate_heatmap(model, image_batch)
    assert heatmap.shape == (_INPUT_HW, _INPUT_HW)
