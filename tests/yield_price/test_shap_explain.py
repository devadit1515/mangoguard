"""Tests for the SHAP explainability wrapper."""

from __future__ import annotations

import numpy as np
import pandas as pd

from mangoguard.yield_price.shap_explain import explain_prediction, top_n_features
from mangoguard.yield_price.yield_xgb import train_yield_model

_N_SAMPLES = 150


def _make_dataset(seed: int = 7):
    rng = np.random.default_rng(seed)
    n = _N_SAMPLES
    df = pd.DataFrame(
        {
            "ndvi": rng.uniform(0, 1, size=n),
            "gdd": rng.uniform(800, 2000, size=n),
            "acreage": rng.uniform(3, 25, size=n),
        }
    )
    y = pd.Series(
        50 * df["ndvi"] + 0.5 * df["gdd"] + 40 * df["acreage"] + rng.normal(0, 30, size=n)
    )
    return df, y


def test_explain_prediction_returns_dict_with_feature_keys():
    df, y = _make_dataset()
    model, _ = train_yield_model(df, y, n_estimators=50, max_depth=3, early_stopping_rounds=10)
    explanation = explain_prediction(model, df.iloc[[0]])
    assert set(explanation.keys()) == set(df.columns)


def test_explain_prediction_accepts_dict_input():
    df, y = _make_dataset()
    model, _ = train_yield_model(df, y, n_estimators=50, max_depth=3, early_stopping_rounds=10)
    features = {col: float(df[col].iloc[0]) for col in df.columns}
    explanation = explain_prediction(model, features, feature_columns=list(df.columns))
    assert set(explanation.keys()) == set(df.columns)


def test_shap_values_are_finite_floats():
    df, y = _make_dataset()
    model, _ = train_yield_model(df, y, n_estimators=50, max_depth=3, early_stopping_rounds=10)
    explanation = explain_prediction(model, df.iloc[[0]])
    for v in explanation.values():
        assert isinstance(v, float)
        assert np.isfinite(v)


def test_top_n_returns_n_items():
    df, y = _make_dataset()
    model, _ = train_yield_model(df, y, n_estimators=50, max_depth=3, early_stopping_rounds=10)
    top = top_n_features(model, df, n=2)
    assert len(top) == 2
    assert all(isinstance(name, str) for name, _ in top)


def test_top_n_sorted_descending():
    df, y = _make_dataset()
    model, _ = train_yield_model(df, y, n_estimators=50, max_depth=3, early_stopping_rounds=10)
    top = top_n_features(model, df, n=3)
    values = [v for _, v in top]
    assert values == sorted(values, reverse=True)


def test_top_n_larger_than_pool_returns_all():
    df, y = _make_dataset()
    model, _ = train_yield_model(df, y, n_estimators=50, max_depth=3, early_stopping_rounds=10)
    top = top_n_features(model, df, n=10)
    assert len(top) == len(df.columns)
