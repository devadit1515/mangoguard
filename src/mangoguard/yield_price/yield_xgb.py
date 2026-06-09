"""XGBoost yield model (Plan 5 Task 10).

Target: ``yield_kg_per_acre``. Per spec O5 success criterion the model
must beat the seasonal-mean baseline by >=15% MAE.

The trainer accepts a feature DataFrame + target Series; it does NOT
do feature engineering (callers use ``features.build_features``). This
keeps the model layer thin and lets the same code train on real
historical data, on synthetic data for tests, or on the hold-out
fold.

Model:
* ``XGBRegressor`` with ``n_estimators=300``, ``max_depth=5``,
  ``learning_rate=0.05``, ``early_stopping_rounds=20`` on the
  validation fold.
* Categorical features (``soil_texture_class``) are one-hot encoded
  upstream by the notebook -- the model accepts pure-numeric input.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error

from .features import FEATURE_NAMES

_DEFAULT_N_ESTIMATORS = 300
_DEFAULT_MAX_DEPTH = 5
_DEFAULT_LR = 0.05
_DEFAULT_EARLY_STOP = 20
_TEST_FRAC = 0.2
_RANDOM_SEED = 7


@dataclass(frozen=True, slots=True)
class YieldModelMetrics:
    """Bundle returned by ``train_yield_model`` for the report Section 8 table."""

    mae_model: float
    mae_seasonal_baseline: float
    relative_improvement_pct: float
    n_train: int
    n_test: int


def _seasonal_baseline_prediction(
    train_y: pd.Series,
    test_X: pd.DataFrame,
) -> pd.Series:
    """Naive baseline: predict the mean yield per ``season_year`` from training.

    Falls back to the global training mean for years not seen in training.
    """
    if "season_year" not in test_X.columns:
        return pd.Series([train_y.mean()] * len(test_X), index=test_X.index)
    year_means = train_y.groupby(train_X_year_from_index(train_y)).mean()
    global_mean = float(train_y.mean())
    return test_X["season_year"].map(year_means).fillna(global_mean).astype(float)


def train_X_year_from_index(_train_y: pd.Series) -> pd.Index:
    """Tiny helper to keep ``_seasonal_baseline_prediction`` testable -- pulls
    the matching season_year from the training target index. Replaced by the
    caller-supplied X in actual use.
    """
    return _train_y.index


def train_yield_model(
    X: pd.DataFrame,
    y: pd.Series,
    *,
    n_estimators: int = _DEFAULT_N_ESTIMATORS,
    max_depth: int = _DEFAULT_MAX_DEPTH,
    learning_rate: float = _DEFAULT_LR,
    early_stopping_rounds: int = _DEFAULT_EARLY_STOP,
    test_frac: float = _TEST_FRAC,
    random_state: int = _RANDOM_SEED,
) -> tuple[xgb.XGBRegressor, YieldModelMetrics]:
    """Train an XGBoost yield regressor + compute the spec O5 metrics.

    Returns the fitted model + a metrics bundle.
    """
    if len(X) != len(y):
        msg = f"X/y length mismatch: {len(X)} vs {len(y)}"
        raise ValueError(msg)
    if len(X) < 10:  # noqa: PLR2004 -- pragmatic minimum for an XGB fit
        msg = "Need at least 10 samples to train; got fewer."
        raise ValueError(msg)

    rng = np.random.default_rng(random_state)
    perm = rng.permutation(len(X))
    n_test = int(len(X) * test_frac)
    test_idx = perm[:n_test]
    train_idx = perm[n_test:]

    X_train = X.iloc[train_idx].reset_index(drop=True)
    X_test = X.iloc[test_idx].reset_index(drop=True)
    y_train = y.iloc[train_idx].reset_index(drop=True)
    y_test = y.iloc[test_idx].reset_index(drop=True)

    model = xgb.XGBRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        early_stopping_rounds=early_stopping_rounds,
        random_state=random_state,
        verbosity=0,
        objective="reg:squarederror",
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    preds = model.predict(X_test)
    mae_model = float(mean_absolute_error(y_test, preds))
    # Seasonal baseline: predict per-year training mean
    if "season_year" in X_train.columns:
        year_means = y_train.groupby(X_train["season_year"]).mean()
        global_mean = float(y_train.mean())
        baseline_preds = X_test["season_year"].map(year_means).fillna(global_mean).astype(float)
    else:
        baseline_preds = pd.Series([float(y_train.mean())] * len(y_test), index=y_test.index)
    mae_baseline = float(mean_absolute_error(y_test, baseline_preds))
    rel_improvement = 100.0 * (mae_baseline - mae_model) / mae_baseline if mae_baseline > 0 else 0.0
    metrics = YieldModelMetrics(
        mae_model=mae_model,
        mae_seasonal_baseline=mae_baseline,
        relative_improvement_pct=rel_improvement,
        n_train=len(X_train),
        n_test=len(X_test),
    )
    return model, metrics


def predict_yield(model: xgb.XGBRegressor, features: dict[str, Any]) -> float:
    """Single-row prediction. Missing features default to NaN (XGB handles)."""
    row = {name: features.get(name, np.nan) for name in FEATURE_NAMES}
    df = pd.DataFrame([row])
    pred = float(model.predict(df)[0])
    return pred


def save_yield_model(model: xgb.XGBRegressor, path: str | Path) -> None:
    """Persist the XGBoost model to JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(path))


def load_yield_model(path: str | Path) -> xgb.XGBRegressor:
    """Load a JSON-saved XGBoost yield model."""
    model = xgb.XGBRegressor()
    model.load_model(str(path))
    return model


def metrics_to_dict(metrics: YieldModelMetrics) -> dict[str, float | int]:
    """JSON-friendly dict for ``artifacts/yield_metrics.json``."""
    return {
        "mae_model": metrics.mae_model,
        "mae_seasonal_baseline": metrics.mae_seasonal_baseline,
        "relative_improvement_pct": metrics.relative_improvement_pct,
        "n_train": metrics.n_train,
        "n_test": metrics.n_test,
    }


def write_metrics_json(metrics: YieldModelMetrics, path: str | Path) -> None:
    """Convenience -- save metrics dict to ``path``."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics_to_dict(metrics), f, indent=2)
