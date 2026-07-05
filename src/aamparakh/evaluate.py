"""Prediction-quality metrics for dry-matter regression.

RMSEP is the headline (root mean squared error of prediction, in %DM). SEP is its
bias-corrected twin, and RPD (ratio of the reference spread to SEP) is the standard
spectroscopy figure for "is this model useful": RPD below ~1.5 is poor, 2-2.5 is
usable for screening, above 3 is good quantitative work.
"""

from __future__ import annotations

import numpy as np


def rmse(y_true, y_pred) -> float:
    y, p = np.asarray(y_true, float), np.asarray(y_pred, float)
    return float(np.sqrt(np.mean((y - p) ** 2)))


def bias(y_true, y_pred) -> float:
    return float(np.mean(np.asarray(y_pred, float) - np.asarray(y_true, float)))


def r2(y_true, y_pred) -> float:
    y, p = np.asarray(y_true, float), np.asarray(y_pred, float)
    return float(1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2))


def sep(y_true, y_pred) -> float:
    """Standard error of prediction (residual spread with the mean bias removed)."""
    r = np.asarray(y_pred, float) - np.asarray(y_true, float)
    return float(np.sqrt(np.mean((r - r.mean()) ** 2)))


def rpd(y_true, y_pred) -> float:
    return float(np.std(np.asarray(y_true, float), ddof=1) / sep(y_true, y_pred))


def report(y_true, y_pred) -> dict:
    return {
        "rmsep": round(rmse(y_true, y_pred), 4),
        "r2": round(r2(y_true, y_pred), 4),
        "bias": round(bias(y_true, y_pred), 4),
        "sep": round(sep(y_true, y_pred), 4),
        "rpd": round(rpd(y_true, y_pred), 4),
        "n": int(len(y_true)),
    }
