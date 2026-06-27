"""Tests for the single-image inference module."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from mangoguard.disease_detector.infer import (
    DEFAULT_CLASSES,
    DiseasePrediction,
    predict_image,
)


@pytest.fixture
def sample_jpeg(tmp_path):
    path = tmp_path / "leaf.jpg"
    Image.new("RGB", (300, 300), color=(120, 200, 80)).save(path)
    return path


def test_predict_returns_disease_prediction(sample_jpeg):
    pred = predict_image(sample_jpeg)
    assert isinstance(pred, DiseasePrediction)


def test_confidence_in_0_1(sample_jpeg):
    pred = predict_image(sample_jpeg)
    assert 0.0 <= pred.confidence <= 1.0


def test_class_probabilities_sum_to_one(sample_jpeg):
    pred = predict_image(sample_jpeg)
    total = sum(pred.class_probabilities.values())
    assert abs(total - 1.0) < 1e-5


def test_predicted_class_in_default_classes(sample_jpeg):
    pred = predict_image(sample_jpeg)
    assert pred.class_name in DEFAULT_CLASSES


def test_heatmap_overlay_shape(sample_jpeg):
    pred = predict_image(sample_jpeg)
    assert pred.heatmap_overlay.shape == (224, 224, 3)
    assert pred.heatmap_overlay.dtype == np.uint8


def test_low_confidence_flag_set_for_untrained_model(sample_jpeg):
    """An untrained model gives ~uniform probs -> max ~0.20 -> low_confidence True."""
    pred = predict_image(sample_jpeg)
    if pred.confidence < 0.8:
        assert pred.low_confidence is True


def test_missing_image_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="Image not found"):
        predict_image(tmp_path / "no_such_image.jpg")


def test_custom_classes_kwarg_routes_through(sample_jpeg):
    pred = predict_image(sample_jpeg, classes=("a", "b", "c"))
    assert pred.class_name in ("a", "b", "c")
    assert set(pred.class_probabilities.keys()) == {"a", "b", "c"}


def test_predict_handles_grayscale_image_via_rgb_convert(tmp_path):
    """Grayscale images should be converted to RGB internally."""
    path = tmp_path / "gray.jpg"
    Image.new("L", (200, 200), color=120).save(path)
    pred = predict_image(path)
    assert pred.heatmap_overlay.shape == (224, 224, 3)
