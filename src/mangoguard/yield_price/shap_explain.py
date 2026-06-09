"""SHAP explainability wrapper (Plan 5 Task 12).

Thin wrapper around ``shap.TreeExplainer`` so the Streamlit yield/price
page can show:
* per-prediction feature contributions (waterfall plot data),
* global top-N features by mean(|SHAP value|).

These per-prediction explanations are essential for the CREST 4.3
creativity claim that the yield/price models are decision-useful (not
black-box) and for 4.5 clear writing.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import shap


def explain_prediction(
    model: Any,
    features: dict[str, float] | pd.DataFrame,
    feature_columns: list[str] | None = None,
) -> dict[str, float]:
    """Return ``{feature_name: shap_value}`` for a single prediction.

    Args:
        model: An XGBoost regressor (tree explainer-compatible).
        features: Either a flat dict or a 1-row DataFrame.
        feature_columns: Optional ordering for dict inputs. When ``None``
            and the features arg is a dict, columns come from dict keys.
    """
    if isinstance(features, dict):
        cols = feature_columns or list(features.keys())
        row = pd.DataFrame([{c: features.get(c, np.nan) for c in cols}], columns=cols)
    else:
        row = features.copy()
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(row)
    if isinstance(shap_values, list):
        # multi-output (classification) -- pick first; regression is single-output already
        shap_values = shap_values[0]
    values = np.asarray(shap_values).flatten()
    return {col: float(val) for col, val in zip(row.columns, values, strict=True)}


def top_n_features(
    model: Any,
    X_train: pd.DataFrame,
    n: int = 5,
) -> list[tuple[str, float]]:
    """Global top-N features by mean(|SHAP|) across ``X_train``.

    Returns a list of ``(feature_name, mean_abs_shap)`` sorted descending.
    """
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_train)
    if isinstance(shap_values, list):
        shap_values = shap_values[0]
    mean_abs = np.mean(np.abs(np.asarray(shap_values)), axis=0)
    ranking = sorted(
        zip(X_train.columns, mean_abs, strict=True),
        key=lambda kv: -float(kv[1]),
    )
    return [(name, float(val)) for name, val in ranking[:n]]
