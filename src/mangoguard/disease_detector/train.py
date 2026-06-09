"""Two-phase fine-tuning trainer (Plan 5 Task 4).

Phase 1: backbone frozen, head trained at ``lr=1e-3`` for 5 epochs.
Phase 2: full unfreeze, ``lr=1e-5`` for 15 epochs, early-stop patience 5.

Loss: ``CrossEntropyLoss`` with class weights from
``sklearn.utils.class_weight.compute_class_weight`` to handle the
heavy class imbalance in the Visit-1 dataset (healthy + sooty_mould
dominate).

The trainer is split into ``train_phase1`` / ``train_phase2`` so the
Colab notebook can stop between phases for inspection. The
``train_full_pipeline`` convenience wraps both phases + checkpoint save.

Heavy lifting (actual MangoLeafBD fine-tune) belongs in
``notebooks/03_disease_detector_training.ipynb`` -- this module is
the importable + testable engine those notebooks call.
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import torch
from torch import nn, optim
from torch.utils.data import DataLoader, Dataset

from .model import build_model, freeze_backbone, unfreeze_backbone

logger = logging.getLogger(__name__)

_PHASE1_EPOCHS = 5
_PHASE1_LR = 1e-3
_PHASE2_EPOCHS = 15
_PHASE2_LR = 1e-5
_DEFAULT_PATIENCE = 5


@dataclass(frozen=True, slots=True)
class TrainerConfig:
    """Hyperparameter bundle. Override individual fields from the notebook."""

    phase1_epochs: int = _PHASE1_EPOCHS
    phase1_lr: float = _PHASE1_LR
    phase2_epochs: int = _PHASE2_EPOCHS
    phase2_lr: float = _PHASE2_LR
    patience: int = _DEFAULT_PATIENCE
    batch_size: int = 32


def compute_class_weights(
    targets: list[int],
    n_classes: int,
) -> torch.Tensor:
    """Per-class weights ~ inverse frequency. Avoids 0-division when a class
    is missing from the training fold by using a smoothed denominator.
    """
    counter = Counter(targets)
    total = sum(counter.values())
    weights = []
    for cls in range(n_classes):
        cnt = counter.get(cls, 0) + 1  # smoothing
        weights.append(total / (n_classes * cnt))
    return torch.tensor(weights, dtype=torch.float32)


def _run_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: optim.Optimizer,
    loss_fn: nn.Module,
    device: torch.device,
    *,
    train: bool,
) -> tuple[float, float]:
    """Run one epoch; return (mean_loss, accuracy)."""
    model.train(train)
    total_loss = 0.0
    correct = 0
    seen = 0
    for x, y in loader:
        x_dev = x.to(device)
        y_dev = y.to(device)
        if train:
            optimizer.zero_grad()
        logits = model(x_dev)
        loss = loss_fn(logits, y_dev)
        if train:
            loss.backward()
            optimizer.step()
        total_loss += float(loss.item()) * x_dev.size(0)
        correct += int((logits.argmax(dim=1) == y_dev).sum().item())
        seen += x_dev.size(0)
    return total_loss / max(seen, 1), correct / max(seen, 1)


def train_phase1(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    *,
    n_classes: int,
    config: TrainerConfig | None = None,
    device: str = "cpu",
) -> dict[str, list[float]]:
    """Head-only training (backbone frozen).

    Returns dict of per-epoch metrics so the notebook can plot training curves.
    """
    config = config or TrainerConfig()
    dev = torch.device(device)
    freeze_backbone(model)
    model.to(dev)

    targets = _flatten_targets(train_loader.dataset)
    class_weights = compute_class_weights(targets, n_classes).to(dev)
    loss_fn = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = optim.Adam(
        [p for p in model.parameters() if p.requires_grad],
        lr=config.phase1_lr,
    )

    history: dict[str, list[float]] = {
        "train_loss": [],
        "train_acc": [],
        "val_loss": [],
        "val_acc": [],
    }
    for epoch in range(config.phase1_epochs):
        train_loss, train_acc = _run_epoch(model, train_loader, optimizer, loss_fn, dev, train=True)
        val_loss, val_acc = _run_epoch(model, val_loader, optimizer, loss_fn, dev, train=False)
        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        logger.info(
            "phase1 epoch %d/%d: train_loss=%.4f train_acc=%.4f val_loss=%.4f val_acc=%.4f",
            epoch + 1,
            config.phase1_epochs,
            train_loss,
            train_acc,
            val_loss,
            val_acc,
        )
    return history


def train_phase2(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    *,
    n_classes: int,
    config: TrainerConfig | None = None,
    device: str = "cpu",
    checkpoint_path: Path | str | None = None,
) -> dict[str, list[float]]:
    """Full-model fine-tuning. Saves best-val-acc checkpoint when path given."""
    config = config or TrainerConfig()
    dev = torch.device(device)
    unfreeze_backbone(model)
    model.to(dev)

    targets = _flatten_targets(train_loader.dataset)
    class_weights = compute_class_weights(targets, n_classes).to(dev)
    loss_fn = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = optim.Adam(model.parameters(), lr=config.phase2_lr)

    history: dict[str, list[float]] = {
        "train_loss": [],
        "train_acc": [],
        "val_loss": [],
        "val_acc": [],
    }
    best_val_acc = -1.0
    patience_left = config.patience
    for epoch in range(config.phase2_epochs):
        train_loss, train_acc = _run_epoch(model, train_loader, optimizer, loss_fn, dev, train=True)
        val_loss, val_acc = _run_epoch(model, val_loader, optimizer, loss_fn, dev, train=False)
        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        logger.info(
            "phase2 epoch %d/%d: train_loss=%.4f val_acc=%.4f",
            epoch + 1,
            config.phase2_epochs,
            train_loss,
            val_acc,
        )
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_left = config.patience
            if checkpoint_path is not None:
                ckpt_path = Path(checkpoint_path)
                ckpt_path.parent.mkdir(parents=True, exist_ok=True)
                torch.save(model.state_dict(), ckpt_path)
        else:
            patience_left -= 1
            if patience_left <= 0:
                logger.info("phase2 early stop at epoch %d", epoch + 1)
                break
    return history


def train_full_pipeline(
    train_loader: DataLoader,
    val_loader: DataLoader,
    *,
    n_classes: int,
    config: TrainerConfig | None = None,
    device: str = "cpu",
    checkpoint_path: Path | str | None = None,
) -> tuple[nn.Module, dict[str, dict[str, list[float]]]]:
    """Convenience: build model, run phase 1 then phase 2."""
    model = build_model(n_classes=n_classes, freeze_backbone=True)
    h1 = train_phase1(
        model,
        train_loader,
        val_loader,
        n_classes=n_classes,
        config=config,
        device=device,
    )
    h2 = train_phase2(
        model,
        train_loader,
        val_loader,
        n_classes=n_classes,
        config=config,
        device=device,
        checkpoint_path=checkpoint_path,
    )
    return model, {"phase1": h1, "phase2": h2}


def _flatten_targets(dataset: Dataset) -> list[int]:
    """Extract integer targets from an ImageFolder/Subset for class weighting."""
    from torch.utils.data import Subset
    from torchvision.datasets import ImageFolder

    if isinstance(dataset, Subset):
        base = dataset.dataset
        if isinstance(base, ImageFolder):
            return [base.targets[i] for i in dataset.indices]
        return [int(dataset[i][1]) for i in range(len(dataset))]
    if isinstance(dataset, ImageFolder):
        return list(dataset.targets)
    return [int(dataset[i][1]) for i in range(len(dataset))]
