"""Smoke test for the two-phase trainer.

Runs 1 epoch on 20 random-tensor "images" via a tiny custom Dataset.
Asserts the loss decreases (or at least is finite) and that the phase
sequence runs without crashing. Real training happens in
``notebooks/03_disease_detector_training.ipynb``.
"""

from __future__ import annotations

import pytest
import torch
from torch.utils.data import DataLoader, Dataset

from mangoguard.disease_detector.model import build_model
from mangoguard.disease_detector.train import (
    TrainerConfig,
    compute_class_weights,
    train_phase1,
    train_phase2,
)

_N_CLASSES = 3
_N_SAMPLES = 20
_INPUT_HW = 64  # small for speed; model still accepts (will adaptive-pool)


class _RandomTensorDataset(Dataset):
    """A dataset of (rand_img, integer_label) for smoke testing."""

    def __init__(self, n: int, n_classes: int, hw: int = 224) -> None:
        rng = torch.Generator().manual_seed(7)
        self.images = torch.randn(n, 3, hw, hw, generator=rng)
        self.labels = torch.randint(0, n_classes, (n,), generator=rng).tolist()
        self.targets = self.labels  # for compute_class_weights path
        self.classes = [str(i) for i in range(n_classes)]

    def __len__(self) -> int:
        return self.images.shape[0]

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        return self.images[idx], self.labels[idx]


@pytest.fixture
def loaders():
    ds = _RandomTensorDataset(_N_SAMPLES, _N_CLASSES, hw=_INPUT_HW)
    train = DataLoader(ds, batch_size=4, shuffle=True)
    val = DataLoader(ds, batch_size=4, shuffle=False)
    return train, val


def test_compute_class_weights_returns_n_class_tensor():
    weights = compute_class_weights([0, 0, 1, 1, 2], n_classes=3)
    assert weights.shape == (3,)
    assert torch.isfinite(weights).all()


def test_compute_class_weights_handles_missing_class():
    """A class with zero samples must still get a finite weight (smoothing)."""
    weights = compute_class_weights([0, 0, 1, 1], n_classes=3)
    assert torch.isfinite(weights).all()
    assert weights[2] > 0


def test_phase1_runs_one_epoch(loaders):
    train, val = loaders
    model = build_model(n_classes=_N_CLASSES, freeze_backbone=True)
    cfg = TrainerConfig(phase1_epochs=1, batch_size=4)
    history = train_phase1(model, train, val, n_classes=_N_CLASSES, config=cfg)
    assert len(history["train_loss"]) == 1
    assert torch.isfinite(torch.tensor(history["train_loss"][0])).item()


def test_phase2_runs_one_epoch(loaders):
    train, val = loaders
    model = build_model(n_classes=_N_CLASSES, freeze_backbone=False)
    cfg = TrainerConfig(phase2_epochs=1, patience=10, batch_size=4)
    history = train_phase2(model, train, val, n_classes=_N_CLASSES, config=cfg)
    assert len(history["train_loss"]) == 1


def test_phase2_saves_checkpoint(tmp_path, loaders):
    train, val = loaders
    model = build_model(n_classes=_N_CLASSES, freeze_backbone=False)
    cfg = TrainerConfig(phase2_epochs=1, patience=10, batch_size=4)
    ckpt = tmp_path / "ckpt.pth"
    train_phase2(
        model,
        train,
        val,
        n_classes=_N_CLASSES,
        config=cfg,
        checkpoint_path=ckpt,
    )
    assert ckpt.exists()
    state = torch.load(ckpt, map_location="cpu", weights_only=True)
    assert isinstance(state, dict)
    assert any("head" in k for k in state)
