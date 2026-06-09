"""Tests for the MangoLeafBD + Alphonso Visit-1 dataset loaders.

Builds a tiny synthetic ImageFolder on a tmp_path so the loader can be
exercised without downloading the real dataset.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from mangoguard.disease_detector.data import (
    class_counts,
    load_alphonso_visit1,
    load_mangoleafbd,
)


def _seed_image_folder(
    root: Path,
    classes: list[str],
    per_class: int,
    size: tuple[int, int] = (32, 32),
) -> None:
    """Write ``per_class`` solid-color JPEGs per class under ``root/class/``."""
    for i, cls in enumerate(classes):
        cls_dir = root / cls
        cls_dir.mkdir(parents=True, exist_ok=True)
        color = (i * 30 % 256, (i * 60) % 256, (i * 90) % 256)
        for j in range(per_class):
            img = Image.new("RGB", size, color=color)
            img.save(cls_dir / f"img_{j:03d}.jpg")


_MANGOLEAFBD_CLASSES = [
    "Anthracnose",
    "Bacterial_Canker",
    "Cutting_Weevil",
    "Die_Back",
    "Gall_Midge",
    "Healthy",
    "Powdery_Mildew",
    "Sooty_Mould",
]

_ALPHONSO_CLASSES = ["anthracnose", "powdery_mildew", "hopper", "sooty_mould", "healthy"]


def test_mangoleafbd_loader_returns_3_splits(tmp_path):
    _seed_image_folder(tmp_path, _MANGOLEAFBD_CLASSES, per_class=10)
    train, val, test = load_mangoleafbd(tmp_path)
    assert len(train) > 0
    assert len(val) > 0
    assert len(test) > 0


def test_mangoleafbd_loader_split_sums_to_total(tmp_path):
    _seed_image_folder(tmp_path, _MANGOLEAFBD_CLASSES, per_class=10)
    train, val, test = load_mangoleafbd(tmp_path)
    total_seeded = 8 * 10
    assert len(train) + len(val) + len(test) == total_seeded


def test_mangoleafbd_returns_8_classes(tmp_path):
    _seed_image_folder(tmp_path, _MANGOLEAFBD_CLASSES, per_class=5)
    train, _, _ = load_mangoleafbd(tmp_path)
    counts = class_counts(train)
    assert len(counts) == 8


def test_mangoleafbd_missing_root_raises():
    with pytest.raises(FileNotFoundError, match="MangoLeafBD root not found"):
        load_mangoleafbd("/path/does/not/exist")


def test_mangoleafbd_split_deterministic_with_seed(tmp_path):
    _seed_image_folder(tmp_path, _MANGOLEAFBD_CLASSES, per_class=10)
    a_train, _, _ = load_mangoleafbd(tmp_path, seed=42)
    b_train, _, _ = load_mangoleafbd(tmp_path, seed=42)
    assert list(a_train.indices) == list(b_train.indices)


def test_alphonso_loader_returns_2_splits(tmp_path):
    _seed_image_folder(tmp_path, _ALPHONSO_CLASSES, per_class=8)
    train, test = load_alphonso_visit1(tmp_path)
    assert len(train) + len(test) == 5 * 8
    assert len(train) > len(test)


def test_alphonso_returns_5_classes(tmp_path):
    _seed_image_folder(tmp_path, _ALPHONSO_CLASSES, per_class=5)
    train, _ = load_alphonso_visit1(tmp_path)
    counts = class_counts(train)
    assert len(counts) == 5


def test_alphonso_missing_root_raises():
    with pytest.raises(FileNotFoundError, match="Alphonso Visit-1 root not found"):
        load_alphonso_visit1("/path/does/not/exist")


def test_alphonso_split_deterministic_with_seed(tmp_path):
    _seed_image_folder(tmp_path, _ALPHONSO_CLASSES, per_class=10)
    a_train, _ = load_alphonso_visit1(tmp_path, seed=42)
    b_train, _ = load_alphonso_visit1(tmp_path, seed=42)
    assert list(a_train.indices) == list(b_train.indices)


def test_train_image_tensor_shape(tmp_path):
    _seed_image_folder(tmp_path, _ALPHONSO_CLASSES, per_class=4)
    train, _ = load_alphonso_visit1(tmp_path)
    img, _ = train[0]
    assert img.shape == (3, 224, 224)


def test_class_counts_on_subset(tmp_path):
    _seed_image_folder(tmp_path, _ALPHONSO_CLASSES, per_class=10)
    train, _ = load_alphonso_visit1(tmp_path)
    counts = class_counts(train)
    assert all(v >= 1 for v in counts.values())
