"""Tests for PPI weight calibration."""

from __future__ import annotations

import random

import pytest

from mangoguard.risk.calibration import calibrate_weights
from mangoguard.risk.ppi import DEFAULT_WEIGHTS

# Skip the whole module if sklearn is not installed -- the calibrator
# returns defaults in that case but the high-fidelity tests need AUC.
pytest.importorskip("sklearn.metrics")


def _perfect_anth_separable(
    n: int = 60,
) -> tuple[list[tuple[float, float, float]], list[int]]:
    """Half rows have high anth + outbreak=1; half have low anth + outbreak=0.

    PM and hop are random noise. Only anth predicts the outbreak, so the
    calibrator should assign nearly all weight to ``anth``.
    """
    rng = random.Random(42)
    rows: list[tuple[float, float, float]] = []
    labels: list[int] = []
    for i in range(n):
        if i % 2 == 0:
            rows.append((0.9, rng.random(), rng.random()))
            labels.append(1)
        else:
            rows.append((0.1, rng.random(), rng.random()))
            labels.append(0)
    return rows, labels


def _perfect_hop_separable(
    n: int = 60,
) -> tuple[list[tuple[float, float, float]], list[int]]:
    """Hopper component perfectly separates labels."""
    rng = random.Random(7)
    rows: list[tuple[float, float, float]] = []
    labels: list[int] = []
    for i in range(n):
        if i % 2 == 0:
            rows.append((rng.random(), rng.random(), 0.95))
            labels.append(1)
        else:
            rows.append((rng.random(), rng.random(), 0.05))
            labels.append(0)
    return rows, labels


def test_returns_weights_dict_with_expected_keys():
    rows, labels = _perfect_anth_separable()
    weights = calibrate_weights(rows, labels)
    assert set(weights.keys()) == {"anth", "pm", "hop"}


def test_returned_weights_sum_to_1():
    rows, labels = _perfect_anth_separable()
    weights = calibrate_weights(rows, labels)
    s = weights["anth"] + weights["pm"] + weights["hop"]
    assert s == pytest.approx(1.0, abs=1e-3)


def test_returned_weights_are_non_negative():
    rows, labels = _perfect_anth_separable()
    weights = calibrate_weights(rows, labels)
    assert weights["anth"] >= 0.0
    assert weights["pm"] >= 0.0
    assert weights["hop"] >= 0.0


def test_perfect_anth_data_yields_high_anth_weight():
    """If only anthracnose predicts outbreaks, anth weight should dominate."""
    rows, labels = _perfect_anth_separable()
    weights = calibrate_weights(rows, labels)
    assert weights["anth"] > 0.5, f"expected anth > 0.5, got {weights}"


def test_perfect_hop_data_yields_high_hop_weight():
    """If only hopper predicts outbreaks, hop weight should dominate."""
    rows, labels = _perfect_hop_separable()
    weights = calibrate_weights(rows, labels)
    assert weights["hop"] > 0.5, f"expected hop > 0.5, got {weights}"


def test_falls_back_to_defaults_when_under_min_samples():
    """<30 rows -> return DEFAULT_WEIGHTS unchanged."""
    short_rows = [(0.9, 0.1, 0.1), (0.1, 0.1, 0.1), (0.5, 0.5, 0.5)]
    short_labels = [1, 0, 1]
    weights = calibrate_weights(short_rows, short_labels)
    assert weights == DEFAULT_WEIGHTS


def test_falls_back_to_defaults_when_single_class_labels():
    """All-positive or all-negative labels -> defaults."""
    rng = random.Random(1)
    rows = [(rng.random(), rng.random(), rng.random()) for _ in range(50)]
    all_positive = [1] * 50
    weights = calibrate_weights(rows, all_positive)
    assert weights == DEFAULT_WEIGHTS


def test_length_mismatch_raises_value_error():
    rows = [(0.5, 0.3, 0.2)] * 30
    bad_labels = [1] * 25
    with pytest.raises(ValueError, match="length"):
        calibrate_weights(rows, bad_labels)


def test_accepts_dataframe_input():
    """DataFrame with anth/pm/hop columns must be coerced."""
    pd = pytest.importorskip("pandas")
    rows, labels = _perfect_anth_separable()
    df = pd.DataFrame(rows, columns=["anth", "pm", "hop"])
    label_series = pd.Series(labels)
    weights = calibrate_weights(df, label_series)
    assert weights["anth"] > 0.5


def test_calibrated_weights_differ_from_defaults_on_real_signal():
    """A signal-bearing dataset should NOT return exactly the defaults."""
    rows, labels = _perfect_anth_separable()
    weights = calibrate_weights(rows, labels)
    differs = any(abs(weights[k] - DEFAULT_WEIGHTS[k]) > 0.05 for k in DEFAULT_WEIGHTS)
    assert differs, f"expected calibrated weights to differ, got {weights}"
