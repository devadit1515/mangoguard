"""MobileNetV3-Small backbone + custom classification head.

Per Plan 5 Task 3: efficient backbone (chosen over DenseNet201 despite
~2% lower accuracy on MangoLeafBD) because the on-phone inference
target for the Streamlit "upload a leaf photo" experience needs sub-
second response on entry-level Android devices.

Custom head per spec section 4.5 Module 1::

    AdaptiveAvgPool2d(1) -> Flatten -> Linear(576, 256) -> ReLU
    -> Dropout(0.5) -> Linear(256, n_classes)

Two-phase fine-tune workflow:
* Phase 1 (5 epochs, lr=1e-3): backbone frozen, train head only.
* Phase 2 (15 epochs, lr=1e-5, patience 5): full unfreeze.

The ``build_model`` factory accepts ``freeze_backbone`` so the trainer
(Plan 5 Task 4) can flip between the two phases without rebuilding.
"""

from __future__ import annotations

import torch
from torch import nn
from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small

# Last conv block of MobileNetV3-Small outputs 576 channels; this is the
# input dimension to our custom head.
_MOBILENETV3_SMALL_BACKBONE_OUT = 576
_HEAD_HIDDEN = 256
_HEAD_DROPOUT = 0.5


def build_model(n_classes: int, *, freeze_backbone: bool = True) -> nn.Module:
    """Construct a MobileNetV3-Small + custom head for ``n_classes``.

    Args:
        n_classes: 8 for MangoLeafBD (Phase A), 5 for Alphonso Visit-1
            (Phase B). The trainer maps MangoLeafBD's 8 classes down to
            Alphonso's 5 between phases (see ``train.py``).
        freeze_backbone: When True (Phase 1) all backbone params have
            ``requires_grad = False``. The trainer flips this for Phase 2.

    Returns:
        nn.Module with input shape ``(B, 3, 224, 224)`` and output
        ``(B, n_classes)``.
    """
    weights = MobileNet_V3_Small_Weights.IMAGENET1K_V1
    backbone = mobilenet_v3_small(weights=weights)
    # Strip the original classifier head and keep only the features block.
    backbone.classifier = nn.Identity()
    if freeze_backbone:
        for param in backbone.parameters():
            param.requires_grad = False

    head = nn.Sequential(
        nn.Linear(_MOBILENETV3_SMALL_BACKBONE_OUT, _HEAD_HIDDEN),
        nn.ReLU(inplace=True),
        nn.Dropout(_HEAD_DROPOUT),
        nn.Linear(_HEAD_HIDDEN, n_classes),
    )

    return _MangoClassifier(backbone, head)


class _MangoClassifier(nn.Module):
    """MobileNetV3-Small + classification head composite.

    Kept private to discourage import-from-test patterns; use the
    ``build_model`` factory.
    """

    def __init__(self, backbone: nn.Module, head: nn.Module) -> None:
        super().__init__()
        self.backbone = backbone
        self.head = head

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.backbone(x)
        return self.head(features)


def unfreeze_backbone(model: nn.Module) -> None:
    """Used by Phase 2 of the trainer to switch from head-only -> full fine-tune."""
    for param in model.parameters():
        param.requires_grad = True


def freeze_backbone(model: nn.Module) -> None:
    """Re-freeze the backbone (used by tests + when reverting to feature-extractor mode)."""
    classifier_module = model.head if hasattr(model, "head") else None
    for name, param in model.named_parameters():
        if classifier_module is not None and name.startswith("head."):
            param.requires_grad = True
        else:
            param.requires_grad = False
