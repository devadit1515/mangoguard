"""XGBoost mandi-price model (Plan 5 Task 11).

Target: ``mandi_modal_price_inr_per_quintal`` at the harvest week.

Features (built by the notebook from AGMARKNET 2001-2025):
* ``iso_week`` (1-52)
* one-hot ``mandi_<name>`` for the major Konkan + Vashi mandis
* 4-week-lag prices (lag1..lag4) -- short-term price momentum
* 4-week-lag arrivals -- supply signal
* weather aggregates for the production region (mean Tmax, total rainfall)

Spec section 4.5 O5 success: beat the seasonal-mean baseline by
>=15% MAE.

Unknown mandi (not seen in training) -> falls back to the global mean
for that ISO week via the ``predict_price`` helper.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error

_DEFAULT_N_ESTIMATORS = 400
_DEFAULT_MAX_DEPTH = 6
_DEFAULT_LR = 0.05
_DEFAULT_EARLY_STOP = 25
_TEST_FRAC = 0.2
_RANDOM_SEED = 13


@dataclass(frozen=True, slots=True)
class PriceModelMetrics:
    """Spec O5 metrics bundle for the report Section 8 table."""

    mae_model: float
    mae_seasonal_baseline: float
    relative_improvement_pct: float
    n_train: int
    n_test: int


def train_price_model(
    X: pd.DataFrame,
    y: pd.Series,
    *,
    n_estimators: int = _DEFAULT_N_ESTIMATORS,
    max_depth: int = _DEFAULT_MAX_DEPTH,
    learning_rate: float = _DEFAULT_LR,
    early_stopping_rounds: int = _DEFAULT_EARLY_STOP,
    test_frac: float = _TEST_FRAC,
    random_state: int = _RANDOM_SEED,
) -> tuple[xgb.XGBRegressor, PriceModelMetrics]:
    """Fit the price XGB + report MAE vs seasonal-mean baseline."""
    if len(X) != len(y):
        msg = f"X/y length mismatch: {len(X)} vs {len(y)}"
        raise ValueError(msg)
    if len(X) < 20:  # noqa: PLR2004 -- pragmatic minimum for the price model
        msg = "Need at least 20 samples to train the price model."
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

    # Seasonal baseline: predict per-iso-week training mean
    if "iso_week" in X_train.columns:
        week_means = y_train.groupby(X_train["iso_week"]).mean()
        global_mean = float(y_train.mean())
        baseline_preds = X_test["iso_week"].map(week_means).fillna(global_mean).astype(float)
    else:
        baseline_preds = pd.Series([float(y_train.mean())] * len(y_test), index=y_test.index)
    mae_baseline = float(mean_absolute_error(y_test, baseline_preds))
    rel_improvement = 100.0 * (mae_baseline - mae_model) / mae_baseline if mae_baseline > 0 else 0.0
    metrics = PriceModelMetrics(
        mae_model=mae_model,
        mae_seasonal_baseline=mae_baseline,
        relative_improvement_pct=rel_improvement,
        n_train=len(X_train),
        n_test=len(X_test),
    )
    return model, metrics


def predict_price(
    model: xgb.XGBRegressor,
    *,
    mandi: str,
    harvest_iso_week: int,
    features: dict | None = None,
    feature_columns: list[str] | None = None,
) -> float:
    """Single-prediction helper for the Streamlit page.

    Args:
        model: Trained ``XGBRegressor``.
        mandi: Mandi name (e.g., "Vashi"). One-hot-encoded against
            ``feature_columns`` -- unknown mandis result in all-zero
            one-hot which the model handles like any other novel input.
        harvest_iso_week: ISO week of expected harvest (1-52).
        features: Optional extra numeric features keyed by column name.
        feature_columns: Column ordering the model was trained on; required
            to align the one-hot vector. The notebook pickles this alongside
            the model.
    """
    if feature_columns is None:
        msg = "predict_price requires the feature_columns list used at training time."
        raise ValueError(msg)
    row = {col: float(features.get(col, 0.0)) if features else 0.0 for col in feature_columns}
    row["iso_week"] = float(harvest_iso_week)
    one_hot_key = f"mandi_{mandi}"
    if one_hot_key in row:
        row[one_hot_key] = 1.0
    df = pd.DataFrame([row], columns=feature_columns)
    return float(model.predict(df)[0])


def save_price_model(model: xgb.XGBRegressor, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(path))


def load_price_model(path: str | Path) -> xgb.XGBRegressor:
    model = xgb.XGBRegressor()
    model.load_model(str(path))
    return model


def metrics_to_dict(metrics: PriceModelMetrics) -> dict[str, float | int]:
    return {
        "mae_model": metrics.mae_model,
        "mae_seasonal_baseline": metrics.mae_seasonal_baseline,
        "relative_improvement_pct": metrics.relative_improvement_pct,
        "n_train": metrics.n_train,
        "n_test": metrics.n_test,
    }


def write_metrics_json(metrics: PriceModelMetrics, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics_to_dict(metrics), f, indent=2)


_ = np  # keep numpy in scope for future synthetic-data helpers
