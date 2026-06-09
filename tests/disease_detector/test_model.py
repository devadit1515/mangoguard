"""Tests for the MobileNetV3-Small + custom-head architecture."""

from __future__ import annotations

import pytest
import torch

from mangoguard.disease_detector.model import (
    build_model,
    freeze_backbone,
    unfreeze_backbone,
)

_BATCH = 2
_INPUT_HW = 224
_MANGOLEAFBD_CLASSES = 8
_ALPHONSO_CLASSES = 5


def test_model_accepts_224x224_input():
    model = build_model(n_classes=_MANGOLEAFBD_CLASSES)
    x = torch.randn(_BATCH, 3, _INPUT_HW, _INPUT_HW)
    y = model(x)
    assert y.shape == (_BATCH, _MANGOLEAFBD_CLASSES)


def test_output_shape_matches_n_classes_alphonso():
    model = build_model(n_classes=_ALPHONSO_CLASSES)
    x = torch.randn(_BATCH, 3, _INPUT_HW, _INPUT_HW)
    y = model(x)
    assert y.shape == (_BATCH, _ALPHONSO_CLASSES)


def test_freeze_backbone_locks_base_params():
    """In Phase 1, backbone params should be frozen; head should be trainable."""
    model = build_model(n_classes=_MANGOLEAFBD_CLASSES, freeze_backbone=True)
    backbone_trainable = [p.requires_grad for p in model.backbone.parameters()]
    head_trainable = [p.requires_grad for p in model.head.parameters()]
    assert not any(backbone_trainable), "Phase 1 must freeze backbone"
    assert all(head_trainable), "Phase 1 must keep head trainable"


def test_unfreeze_backbone_unlocks_everything():
    """Phase 2: full unfreeze."""
    model = build_model(n_classes=_MANGOLEAFBD_CLASSES, freeze_backbone=True)
    unfreeze_backbone(model)
    for p in model.parameters():
        assert p.requires_grad


def test_freeze_backbone_helper_keeps_head_trainable():
    """The freeze_backbone helper should refreeze backbone but keep head trainable."""
    model = build_model(n_classes=_MANGOLEAFBD_CLASSES, freeze_backbone=False)
    freeze_backbone(model)
    backbone_trainable = [p.requires_grad for p in model.backbone.parameters()]
    head_trainable = [p.requires_grad for p in model.head.parameters()]
    assert not any(backbone_trainable)
    assert all(head_trainable)


def test_model_runs_on_cpu_without_cuda():
    """Inference must work on CPU -- the Streamlit dashboard target is browser/mobile."""
    model = build_model(n_classes=_MANGOLEAFBD_CLASSES)
    model.eval()
    x = torch.randn(1, 3, _INPUT_HW, _INPUT_HW)
    with torch.no_grad():
        y = model(x)
    assert y.shape == (1, _MANGOLEAFBD_CLASSES)


def test_logits_are_finite():
    """No NaN/Inf in fresh-init forward pass."""
    model = build_model(n_classes=_MANGOLEAFBD_CLASSES)
    x = torch.randn(_BATCH, 3, _INPUT_HW, _INPUT_HW)
    y = model(x)
    assert torch.isfinite(y).all()


def test_softmax_probabilities_sum_to_one():
    model = build_model(n_classes=_MANGOLEAFBD_CLASSES)
    x = torch.randn(_BATCH, 3, _INPUT_HW, _INPUT_HW)
    probs = torch.softmax(model(x), dim=1)
    sums = probs.sum(dim=1)
    assert torch.allclose(sums, torch.ones(_BATCH), atol=1e-5)


@pytest.mark.parametrize("n_classes", [3, 5, 8, 12])
def test_build_model_supports_various_class_counts(n_classes):
    model = build_model(n_classes=n_classes)
    x = torch.randn(1, 3, _INPUT_HW, _INPUT_HW)
    y = model(x)
    assert y.shape == (1, n_classes)
