"""Retrospective backtest of the PPI risk engine against CROPSAP outbreaks.

Per spec section 4.6.1: we score the calibrated PPI from Plan 4 Task 5
against Maharashtra CROPSAP outbreak records (2018-2024) and compare
against two baselines:

* **Seasonal-mean** -- a naive baseline that predicts each ISO week's
  historical mean PPI. Models "what would happen if a farmer ignored
  weather and just looked up the calendar mean."
* **ICAR-CISH calendar** -- predicts 1.0 when the ICAR-CISH schedule
  prescribes a spray for the primary pathogen that week, else 0.0.
  Models "what extension officers tell farmers today."

For each scorer (mangoguard / seasonal / icar_cish) we report

* ROC-AUC -- discrimination between outbreak and non-outbreak windows.
* Precision + recall at the 0.5 probability cutoff.
* Brier score -- mean squared error of probabilistic predictions.

Spec section 4.6.1 success criterion: MangoGuard ROC-AUC must beat
**both** baselines on the held-out 2022-2024 portion of the data.

Input ``historical_obs`` is a long-format DataFrame with columns
``[block_id, date, ppi]`` (computed offline by running ``compute_ppi``
across every (block, day) of the retrospective window). Input
``cropsap_outbreaks`` is a DataFrame with columns ``[block_id, date,
outbreak]`` where ``outbreak`` is 0/1.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)

from .baseline_schedule import get_baseline_recommendation, load_baseline

logger = logging.getLogger(__name__)

_PROB_CUTOFF = 0.5
_PPI_NORMALISER = 100.0  # PPI is in [0, 100]; rescale to [0, 1] for metric APIs
_MIN_CLASSES_FOR_AUC = 2


def _normalise_ppi(series: pd.Series) -> pd.Series:
    return series.astype(float).clip(lower=0.0, upper=_PPI_NORMALISER) / _PPI_NORMALISER


def _seasonal_baseline(ppi_df: pd.DataFrame) -> pd.Series:
    """Per-ISO-week mean PPI across the full history."""
    ppi_df = ppi_df.copy()
    ppi_df["iso_week"] = pd.to_datetime(ppi_df["date"]).dt.isocalendar().week
    weekly_mean = ppi_df.groupby("iso_week")["ppi"].mean().to_dict()
    return ppi_df["iso_week"].map(weekly_mean).astype(float).fillna(ppi_df["ppi"].mean())


def _icar_cish_baseline(ppi_df: pd.DataFrame, pathogen: str = "anthracnose") -> pd.Series:
    """1.0 when the ICAR-CISH calendar prescribes a spray for ``pathogen`` in
    the row's ISO week; else 0.0.

    Loaded once via ``load_baseline`` (cached). This is intentionally
    boolean -- the baseline doesn't carry uncertainty.
    """
    # Materialise the schedule so the lookup is O(1) per row, not O(n_entries).
    load_baseline("icar_cish")  # warm cache
    weeks = pd.to_datetime(ppi_df["date"]).dt.isocalendar().week
    return pd.Series(
        [1.0 if get_baseline_recommendation("icar_cish", int(w), pathogen) else 0.0 for w in weeks],
        index=ppi_df.index,
    )


def _metrics(
    y_true: pd.Series,
    y_score: pd.Series,
) -> dict[str, float]:
    """Compute discrimination + threshold + calibration metrics."""
    if y_true.nunique() < _MIN_CLASSES_FOR_AUC:
        return {
            "roc_auc": float("nan"),
            "avg_precision": float("nan"),
            "precision_at_0_5": float("nan"),
            "recall_at_0_5": float("nan"),
            "brier": float("nan"),
            "n_samples": int(len(y_true)),
        }
    y_score_clipped = y_score.clip(lower=0.0, upper=1.0)
    y_pred_binary = (y_score_clipped >= _PROB_CUTOFF).astype(int)
    return {
        "roc_auc": float(roc_auc_score(y_true, y_score_clipped)),
        "avg_precision": float(average_precision_score(y_true, y_score_clipped)),
        "precision_at_0_5": float(precision_score(y_true, y_pred_binary, zero_division=0)),
        "recall_at_0_5": float(recall_score(y_true, y_pred_binary, zero_division=0)),
        "brier": float(brier_score_loss(y_true, y_score_clipped)),
        "n_samples": int(len(y_true)),
    }


def run_retrospective_backtest(
    historical_obs: pd.DataFrame,
    cropsap_outbreaks: pd.DataFrame,
    *,
    pathogen: str = "anthracnose",
) -> dict[str, Any]:
    """Backtest MangoGuard PPI vs CROPSAP outbreaks + two baselines.

    Args:
        historical_obs: Long-format ``[block_id, date, ppi]`` -- pre-computed
            ``compute_ppi`` outputs across the retrospective window.
        cropsap_outbreaks: Long-format ``[block_id, date, outbreak]`` where
            ``outbreak`` is 0/1.
        pathogen: Primary pathogen the ICAR-CISH baseline is queried for.
            Defaults to ``"anthracnose"`` (Konkan Alphonso's dominant disease).

    Returns:
        Nested dict ``{<scorer>: {<metric>: value}}`` with scorers
        ``"mangoguard"``, ``"seasonal_baseline"``, ``"icar_cish_baseline"``.
        Also includes ``"meta"`` with the merged-DataFrame row count.
    """
    if historical_obs.empty or cropsap_outbreaks.empty:
        msg = "Both historical_obs and cropsap_outbreaks must be non-empty"
        raise ValueError(msg)

    required_obs = {"block_id", "date", "ppi"}
    required_outbreak = {"block_id", "date", "outbreak"}
    if not required_obs.issubset(historical_obs.columns):
        msg = f"historical_obs missing columns: {required_obs - set(historical_obs.columns)}"
        raise ValueError(msg)
    if not required_outbreak.issubset(cropsap_outbreaks.columns):
        msg = (
            "cropsap_outbreaks missing columns: "
            f"{required_outbreak - set(cropsap_outbreaks.columns)}"
        )
        raise ValueError(msg)

    obs = historical_obs.copy()
    obs["date"] = pd.to_datetime(obs["date"])
    out = cropsap_outbreaks.copy()
    out["date"] = pd.to_datetime(out["date"])

    merged = obs.merge(out, on=["block_id", "date"], how="inner")
    if merged.empty:
        logger.warning("retrospective: zero-row inner join -- no overlapping (block, date) pairs")
        return {
            "mangoguard": _metrics(pd.Series([]), pd.Series([])),
            "seasonal_baseline": _metrics(pd.Series([]), pd.Series([])),
            "icar_cish_baseline": _metrics(pd.Series([]), pd.Series([])),
            "meta": {"n_merged_rows": 0},
        }

    y_true = merged["outbreak"].astype(int)
    mangoguard_score = _normalise_ppi(merged["ppi"])
    seasonal_score = _normalise_ppi(_seasonal_baseline(merged))
    icar_score = _icar_cish_baseline(merged, pathogen=pathogen)

    return {
        "mangoguard": _metrics(y_true, mangoguard_score),
        "seasonal_baseline": _metrics(y_true, seasonal_score),
        "icar_cish_baseline": _metrics(y_true, icar_score),
        "meta": {
            "n_merged_rows": int(len(merged)),
            "n_outbreaks": int(y_true.sum()),
            "pathogen": pathogen,
        },
    }
