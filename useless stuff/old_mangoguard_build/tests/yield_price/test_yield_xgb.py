"""Tests for the XGBoost yield model."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from mangoguard.yield_price.yield_xgb import (
    YieldModelMetrics,
    load_yield_model,
    metrics_to_dict,
    predict_yield,
    save_yield_model,
    train_yield_model,
    write_metrics_json,
)

_N_SAMPLES = 200


def _make_synthetic_yield_dataset(n: int, seed: int = 7) -> tuple[pd.DataFrame, pd.Series]:
    rng = np.random.default_rng(seed)
    season_year = rng.choice([2019, 2020, 2021, 2022, 2023, 2024], size=n)
    ndvi_integral = rng.uniform(50.0, 90.0, size=n)
    cum_gdd = rng.uniform(800.0, 2000.0, size=n)
    rainfall = rng.uniform(50.0, 600.0, size=n)
    rh_mean = rng.uniform(50.0, 90.0, size=n)
    acreage = rng.uniform(3.0, 25.0, size=n)
    tree_count = (acreage * 25 + rng.normal(0, 5, size=n)).astype(int)
    age = rng.uniform(5, 30, size=n)
    soil_ph = rng.uniform(5.5, 7.5, size=n)
    prev_yield = rng.uniform(5000.0, 12000.0, size=n)

    # Yield is a function of NDVI integral + GDD + acreage with noise
    target = (
        90 * ndvi_integral
        + 1.2 * cum_gdd
        + 60 * acreage
        + 0.4 * prev_yield
        + rng.normal(0, 800, size=n)
    )

    X = pd.DataFrame(
        {
            "acreage": acreage,
            "tree_count": tree_count,
            "mean_tree_age": age,
            "ndvi_integral_apr_jun": ndvi_integral,
            "cum_gdd_above_10c": cum_gdd,
            "total_rainfall_mm": rainfall,
            "mean_rh_pct": rh_mean,
            "soil_texture_class": rng.integers(0, 3, size=n).astype(float),
            "soil_ph": soil_ph,
            "prev_season_yield_kg_per_acre": prev_yield,
            "season_year": season_year,
        }
    )
    y = pd.Series(target)
    return X, y


def test_train_yield_model_returns_xgb_and_metrics():
    X, y = _make_synthetic_yield_dataset(_N_SAMPLES)
    model, metrics = train_yield_model(X, y)
    assert isinstance(metrics, YieldModelMetrics)
    assert metrics.n_train > metrics.n_test
    assert metrics.mae_model > 0


def test_model_beats_seasonal_mean_on_synthetic_separable_data():
    """The synthetic dataset has a strong NDVI signal; XGB should beat the
    seasonal-mean baseline."""
    X, y = _make_synthetic_yield_dataset(_N_SAMPLES, seed=11)
    _, metrics = train_yield_model(X, y)
    # XGB should at least match baseline -- usually beats by >0% on this signal.
    assert metrics.mae_model <= metrics.mae_seasonal_baseline


def test_predict_yield_returns_float():
    X, y = _make_synthetic_yield_dataset(_N_SAMPLES)
    model, _ = train_yield_model(X, y)
    features = {
        "acreage": 10.0,
        "tree_count": 250,
        "mean_tree_age": 12,
        "ndvi_integral_apr_jun": 70.0,
        "cum_gdd_above_10c": 1500.0,
        "total_rainfall_mm": 300.0,
        "mean_rh_pct": 75.0,
        "soil_texture_class": 1.0,
        "soil_ph": 6.5,
        "prev_season_yield_kg_per_acre": 8500.0,
        "season_year": 2024,
    }
    pred = predict_yield(model, features)
    assert isinstance(pred, float)
    assert pred > 0


def test_save_load_round_trip_preserves_predictions(tmp_path):
    X, y = _make_synthetic_yield_dataset(_N_SAMPLES)
    model, _ = train_yield_model(X, y)
    path = tmp_path / "yield.json"
    save_yield_model(model, path)
    loaded = load_yield_model(path)
    preds_orig = model.predict(X.head(5))
    preds_loaded = loaded.predict(X.head(5))
    np.testing.assert_allclose(preds_orig, preds_loaded, rtol=1e-5)


def test_too_few_samples_raises():
    X = pd.DataFrame({"a": [1.0, 2.0]})
    y = pd.Series([10.0, 20.0])
    with pytest.raises(ValueError, match="at least 10"):
        train_yield_model(X, y)


def test_mismatched_xy_lengths_raise():
    X = pd.DataFrame({"a": list(range(20))})
    y = pd.Series(list(range(10)))
    with pytest.raises(ValueError, match="length mismatch"):
        train_yield_model(X, y)


def test_metrics_to_dict_returns_serializable():
    X, y = _make_synthetic_yield_dataset(_N_SAMPLES)
    _, metrics = train_yield_model(X, y)
    d = metrics_to_dict(metrics)
    assert "mae_model" in d
    assert isinstance(d["n_train"], int)


def test_write_metrics_json_writes_file(tmp_path):
    X, y = _make_synthetic_yield_dataset(_N_SAMPLES)
    _, metrics = train_yield_model(X, y)
    path = tmp_path / "metrics.json"
    write_metrics_json(metrics, path)
    assert path.exists()
    with open(path) as f:
        data = json.load(f)
    assert "mae_model" in data
