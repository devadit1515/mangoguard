"""PPI weight calibration via ROC-AUC grid search.

The PPI combiner (``ppi.py``) folds three pathogen risks via fixed
weights ``{anth: 0.5, pm: 0.3, hop: 0.2}``. Those defaults match
Konkan-Alphonso disease prevalence but are not data-fitted. This
module refits them against the cooperating farmer's retrospective
weather record + CROPSAP outbreak labels, maximizing ROC-AUC.

Algorithm
---------
1. **Coarse grid:** every (w_anth, w_pm, w_hop) on a step-0.1 simplex
   with sum == 1.0. ~66 candidates.
2. **Fine grid:** step-0.01 around the coarse winner (+/- 0.05 in each
   dim).
3. For each candidate: score every (block, week) row by
   ``w * [anth, pm, hop]`` and compute ROC-AUC against the binary
   outbreak label.
4. Return the highest-AUC weights.

Falls back to ``DEFAULT_WEIGHTS`` if sklearn is unavailable, fewer
than 30 rows, single-class labels, or all-AUCs-are-NaN.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mangoguard.risk.ppi import DEFAULT_WEIGHTS

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)

_MIN_SAMPLES = 30
_COARSE_STEP = 0.1
_FINE_STEP = 0.01
_FINE_GRID_RADIUS = 0.05

# Numerical tolerances.
_SIMPLEX_NEG_TOLERANCE = -1e-9  # rounding slack for w_hop derived via 1.0 - w_anth - w_pm
_MIN_CLASSES_FOR_AUC = 2  # ROC-AUC requires at least one positive AND one negative


def _simplex_grid(
    step: float,
    center: tuple[float, float, float] | None = None,
    radius: float | None = None,
) -> list[tuple[float, float, float]]:
    """Enumerate (w_anth, w_pm, w_hop) triples on the unit simplex.

    If ``center`` and ``radius`` are given, restricts to candidates
    within ``radius`` of the center on each axis.
    """
    candidates: list[tuple[float, float, float]] = []
    n_steps = int(round(1.0 / step))
    for i in range(n_steps + 1):
        w_anth = round(i * step, 4)
        for j in range(n_steps - i + 1):
            w_pm = round(j * step, 4)
            w_hop = round(1.0 - w_anth - w_pm, 4)
            if w_hop < _SIMPLEX_NEG_TOLERANCE:
                continue
            w_hop = max(0.0, w_hop)
            if center is not None and radius is not None:
                ca, cp, ch = center
                if abs(w_anth - ca) > radius or abs(w_pm - cp) > radius or abs(w_hop - ch) > radius:
                    continue
            candidates.append((w_anth, w_pm, w_hop))
    return candidates


def _score_weights(
    weights: tuple[float, float, float],
    component_scores: list[tuple[float, float, float]],
    labels: list[int],
) -> float:
    """ROC-AUC for ``w . components`` against binary labels.

    Returns -inf if AUC cannot be computed.
    """
    try:
        from sklearn.metrics import roc_auc_score  # noqa: PLC0415
    except ImportError:
        return float("-inf")

    w_anth, w_pm, w_hop = weights
    scores = [w_anth * a + w_pm * p + w_hop * h for (a, p, h) in component_scores]
    try:
        return float(roc_auc_score(labels, scores))
    except (ValueError, ImportError):
        return float("-inf")


def calibrate_weights(
    component_scores: list[tuple[float, float, float]] | pd.DataFrame,
    labels: list[int] | pd.Series,
) -> dict[str, float]:
    """Grid-search the best (w_anth, w_pm, w_hop) by ROC-AUC.

    Parameters
    ----------
    component_scores
        Per-(block, week) anthracnose / powdery_mildew / hopper risk
        scores in [0, 1]. Either a list of 3-tuples or a DataFrame
        with columns ``["anth", "pm", "hop"]``.
    labels
        Binary outbreak labels (1 = outbreak observed in CROPSAP for
        that taluka-week-pathogen, 0 otherwise). Same length as
        ``component_scores``.

    Returns
    -------
    dict
        ``{"anth": ..., "pm": ..., "hop": ...}`` summing to 1.0.
    """
    rows = _coerce_rows(component_scores)
    label_list = _coerce_labels(labels)

    if len(rows) != len(label_list):
        msg = f"component_scores length {len(rows)} != labels length {len(label_list)}"
        raise ValueError(msg)

    if len(rows) < _MIN_SAMPLES:
        logger.warning(
            "calibrate_weights: only %d rows (< %d minimum); falling back to defaults",
            len(rows),
            _MIN_SAMPLES,
        )
        return dict(DEFAULT_WEIGHTS)

    if len(set(label_list)) < _MIN_CLASSES_FOR_AUC:
        logger.warning(
            "calibrate_weights: labels are single-class (%r); falling back to defaults",
            label_list[0] if label_list else None,
        )
        return dict(DEFAULT_WEIGHTS)

    coarse = _simplex_grid(_COARSE_STEP)
    best_w = (
        DEFAULT_WEIGHTS["anth"],
        DEFAULT_WEIGHTS["pm"],
        DEFAULT_WEIGHTS["hop"],
    )
    best_auc = float("-inf")
    for w in coarse:
        auc = _score_weights(w, rows, label_list)
        if auc > best_auc:
            best_auc = auc
            best_w = w

    if best_auc == float("-inf"):
        logger.warning(
            "calibrate_weights: ROC-AUC unavailable for all candidates "
            "(sklearn missing?); falling back to defaults"
        )
        return dict(DEFAULT_WEIGHTS)

    fine = _simplex_grid(_FINE_STEP, center=best_w, radius=_FINE_GRID_RADIUS)
    for w in fine:
        auc = _score_weights(w, rows, label_list)
        if auc > best_auc:
            best_auc = auc
            best_w = w

    return {"anth": best_w[0], "pm": best_w[1], "hop": best_w[2]}


def _coerce_rows(
    data: list[tuple[float, float, float]] | pd.DataFrame,
) -> list[tuple[float, float, float]]:
    """Accept either list-of-tuples or DataFrame with anth/pm/hop columns."""
    if isinstance(data, list):
        return data
    return list(zip(data["anth"], data["pm"], data["hop"], strict=False))


def _coerce_labels(labels: list[int] | pd.Series) -> list[int]:
    if isinstance(labels, list):
        return labels
    return [int(v) for v in labels]
