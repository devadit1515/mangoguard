"""Tests for the XGBoost mandi-price model."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mangoguard.yield_price.price_xgb import (
    PriceModelMetrics,
    load_price_model,
    metrics_to_dict,
    predict_price,
    save_price_model,
    train_price_model,
)

_N_SAMPLES = 300
_MANDIS = ("Vashi", "Ratnagiri", "Devgad", "Vengurla")


def _make_synthetic_price_dataset(
    n: int, seed: int = 13
) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    rng = np.random.default_rng(seed)
    iso_week = rng.integers(1, 53, size=n)
    mandi_idx = rng.integers(0, len(_MANDIS), size=n)
    mandi_one_hot = np.zeros((n, len(_MANDIS)))
    for i, m in enumerate(mandi_idx):
        mandi_one_hot[i, m] = 1.0
    lag1 = rng.uniform(2000, 12000, size=n)
    lag2 = lag1 + rng.normal(0, 400, size=n)
    lag3 = lag2 + rng.normal(0, 400, size=n)
    lag4 = lag3 + rng.normal(0, 400, size=n)
    arrivals = rng.uniform(50, 1000, size=n)
    tmax = rng.uniform(28, 42, size=n)
    rainfall = rng.uniform(0, 200, size=n)

    # Price = a function of lag1 (strong momentum) + seasonal week + tmax + noise
    price = (
        0.7 * lag1
        + 50 * np.sin(iso_week * 2 * np.pi / 52) * 200
        + 30 * tmax
        + rng.normal(0, 200, size=n)
    )

    data = {
        "iso_week": iso_week.astype(float),
        "lag1_price": lag1,
        "lag2_price": lag2,
        "lag3_price": lag3,
        "lag4_price": lag4,
        "arrivals_quintal": arrivals,
        "mean_tmax_c": tmax,
        "total_rainfall_mm": rainfall,
    }
    for i, m in enumerate(_MANDIS):
        data[f"mandi_{m}"] = mandi_one_hot[:, i]
    X = pd.DataFrame(data)
    return X, pd.Series(price), list(X.columns)


def test_train_price_model_returns_xgb_and_metrics():
    X, y, _ = _make_synthetic_price_dataset(_N_SAMPLES)
    model, metrics = train_price_model(X, y)
    assert isinstance(metrics, PriceModelMetrics)
    assert metrics.mae_model > 0


def test_model_beats_seasonal_mean_on_synthetic():
    X, y, _ = _make_synthetic_price_dataset(_N_SAMPLES, seed=17)
    _, metrics = train_price_model(X, y)
    # XGB should at least tie baseline; usually beats by a wide margin
    assert metrics.mae_model <= metrics.mae_seasonal_baseline


def test_predict_price_returns_float():
    X, y, cols = _make_synthetic_price_dataset(_N_SAMPLES)
    model, _ = train_price_model(X, y)
    features = {col: float(X[col].mean()) for col in cols}
    pred = predict_price(
        model,
        mandi="Vashi",
        harvest_iso_week=18,
        features=features,
        feature_columns=cols,
    )
    assert isinstance(pred, float)
    assert pred > 0


def test_predict_price_unknown_mandi_does_not_crash():
    X, y, cols = _make_synthetic_price_dataset(_N_SAMPLES)
    model, _ = train_price_model(X, y)
    features = {col: float(X[col].mean()) for col in cols}
    pred = predict_price(
        model,
        mandi="UnknownTown",
        harvest_iso_week=20,
        features=features,
        feature_columns=cols,
    )
    assert isinstance(pred, float)


def test_predict_price_requires_feature_columns():
    X, y, _ = _make_synthetic_price_dataset(_N_SAMPLES)
    model, _ = train_price_model(X, y)
    with pytest.raises(ValueError, match="feature_columns"):
        predict_price(model, mandi="Vashi", harvest_iso_week=18)


def test_save_load_round_trip(tmp_path):
    X, y, _ = _make_synthetic_price_dataset(_N_SAMPLES)
    model, _ = train_price_model(X, y)
    path = tmp_path / "price.json"
    save_price_model(model, path)
    loaded = load_price_model(path)
    preds_orig = model.predict(X.head(5))
    preds_loaded = loaded.predict(X.head(5))
    np.testing.assert_allclose(preds_orig, preds_loaded, rtol=1e-5)


def test_too_few_samples_raises():
    X = pd.DataFrame({"iso_week": list(range(15))})
    y = pd.Series(list(range(15)))
    with pytest.raises(ValueError, match="at least 20"):
        train_price_model(X, y)


def test_metrics_to_dict_returns_serializable():
    X, y, _ = _make_synthetic_price_dataset(_N_SAMPLES)
    _, metrics = train_price_model(X, y)
    d = metrics_to_dict(metrics)
    assert "mae_model" in d
