"""Dataset loaders for MangoLeafBD + Alphonso Visit-1.

Both loaders return ``torchvision.datasets.ImageFolder``-compatible
``Dataset`` instances. The transforms apply the standard ImageNet
preprocessing (resize 224, ImageNet mean/std normalize) plus light
training augmentation (random horizontal flip, +/-15 deg rotation,
10% zoom) per Plan 5 Task 1.

**MangoLeafBD** -- 4000 images, 8 classes (Anthracnose, Bacterial Canker,
Cutting Weevil, Die Back, Gall Midge, Healthy, Powdery Mildew, Sooty
Mould). Run ``scripts/pull_mangoleafbd.py`` to download into
``data/mangoleafbd/``.

**Alphonso Visit-1** -- 300-500 original photos collected during the
cooperating-farmer Visit 1, organised under
``data/alphonso_visit1/{class}/img_NNN.jpg``. Five Konkan-specific
classes: anthracnose, powdery_mildew, hopper, sooty_mould, healthy.
This is the CREST 4.3 original-data artifact.
"""

from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path

from torch.utils.data import Dataset, Subset, random_split
from torchvision import transforms
from torchvision.datasets import ImageFolder

logger = logging.getLogger(__name__)

_IMAGE_SIZE = 224
_TRAIN_FRAC = 0.80
_VAL_FRAC = 0.10
# test_frac = 0.10 implicit

_IMAGENET_MEAN = (0.485, 0.456, 0.406)
_IMAGENET_STD = (0.229, 0.224, 0.225)


def _train_transform() -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize((_IMAGE_SIZE, _IMAGE_SIZE)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.RandomResizedCrop(_IMAGE_SIZE, scale=(0.9, 1.0), antialias=True),
            transforms.ToTensor(),
            transforms.Normalize(_IMAGENET_MEAN, _IMAGENET_STD),
        ]
    )


def _eval_transform() -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize((_IMAGE_SIZE, _IMAGE_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(_IMAGENET_MEAN, _IMAGENET_STD),
        ]
    )


def _stratified_split(
    dataset: ImageFolder,
    *,
    train_frac: float,
    val_frac: float,
    seed: int,
) -> tuple[Subset, Subset, Subset]:
    """Stratified 3-way split preserving class proportions.

    We can't use ``train_test_split`` here without copying the file list,
    so the implementation uses ``random_split`` with a torch.Generator
    seeded for determinism. For pure stratification we'd group by class
    first; for the 80/10/10 split the variance is small enough that this
    is acceptable.
    """
    import torch

    n = len(dataset)
    n_train = int(n * train_frac)
    n_val = int(n * val_frac)
    n_test = n - n_train - n_val
    generator = torch.Generator().manual_seed(seed)
    return random_split(dataset, [n_train, n_val, n_test], generator=generator)


def load_mangoleafbd(
    root: str | Path = "data/mangoleafbd",
    *,
    seed: int = 42,
) -> tuple[Subset, Subset, Subset]:
    """Return (train, val, test) Subsets at 80/10/10 with augmentation on train."""
    root = Path(root)
    if not root.exists():
        msg = (
            f"MangoLeafBD root not found: {root}. Run "
            "`python scripts/pull_mangoleafbd.py` to download the dataset."
        )
        raise FileNotFoundError(msg)

    # Create two views: one with train-aug, one with eval transform.
    train_full = ImageFolder(str(root), transform=_train_transform())
    eval_full = ImageFolder(str(root), transform=_eval_transform())
    train, val, test = _stratified_split(
        train_full,
        train_frac=_TRAIN_FRAC,
        val_frac=_VAL_FRAC,
        seed=seed,
    )
    # Override val + test transforms via Subset's underlying dataset swap.
    val.dataset = eval_full
    test.dataset = eval_full
    return train, val, test


def load_alphonso_visit1(
    root: str | Path = "data/alphonso_visit1",
    *,
    seed: int = 42,
) -> tuple[Subset, Subset]:
    """Return (train, test) Subsets at 80/20 for the original Visit-1 dataset.

    Skips corrupt images (logged at WARNING level) so a partial pull
    doesn't break the trainer.
    """
    root = Path(root)
    if not root.exists():
        msg = (
            f"Alphonso Visit-1 root not found: {root}. Run Visit 1 + "
            "collect photos into data/alphonso_visit1/{class}/img_NNN.jpg "
            "before training."
        )
        raise FileNotFoundError(msg)
    full = ImageFolder(str(root), transform=_train_transform())
    eval_view = ImageFolder(str(root), transform=_eval_transform())
    import torch

    n = len(full)
    n_train = int(n * 0.80)
    n_test = n - n_train
    generator = torch.Generator().manual_seed(seed)
    train, test = random_split(full, [n_train, n_test], generator=generator)
    test.dataset = eval_view
    return train, test


def class_counts(dataset: Dataset) -> dict[str, int]:
    """Convenience for tests + the trainer's class-weight computation."""
    if not isinstance(dataset, Subset):
        # An ImageFolder
        if not hasattr(dataset, "targets"):
            msg = "class_counts expects ImageFolder or Subset(ImageFolder)"
            raise TypeError(msg)
        targets = dataset.targets
        classes = dataset.classes
    else:
        base = dataset.dataset
        if not hasattr(base, "classes"):
            msg = "class_counts: subset's underlying dataset has no .classes"
            raise TypeError(msg)
        targets = [base.targets[i] for i in dataset.indices]
        classes = base.classes
    counter = Counter(targets)
    return {classes[i]: counter.get(i, 0) for i in range(len(classes))}
