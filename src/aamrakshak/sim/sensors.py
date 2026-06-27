"""Sensor tiers: turn the truth into the risk score each data source can give.

Four tiers, scored by the same Akem model so the only thing that changes is the
quality and completeness of the inputs:

- **calendar**   -- no weather at all; the score is the seasonal climatology
  (mean infection probability by day-of-season for the region). This is the
  fair "what a fixed calendar implicitly knows" baseline: it captures the
  seasonal trend but nothing day-specific. A purely random scorer would sit at
  AUC 0.50; climatology is a stronger, more honest baseline.
- **free**       -- a free district forecast: spatially smoothed T/RH/sun/wind
  (cannot see one block) and leaf wetness *estimated from RH* (no sensor).
- **node**       -- the AamRakshak node: local, lightly-noisy T/RH and
  *measured* leaf wetness; it borrows sunshine/wind from the free feed because
  it carries no light or wind sensor (an honest hardware limitation).
- **commercial** -- a clean reference station measuring everything locally with
  little noise (the Rs.40k+ device the node is trying to stand in for).

The node leaf-wetness measurement is modelled as the truth plus integrated
hourly-classification error (a small, roughly unbiased noise). The full
per-hour sensor electronics are exercised separately in the bench validation
(``eval/leafwet_validation.py``); here a vectorised approximation keeps the
multi-seed study fast.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from aamrakshak.riskengine.anthracnose import DEFAULT_COEFFS
from aamrakshak.riskengine.leafwetness import estimate_lw_hours_from_rh

TIER_LABELS: dict[str, str] = {
    "calendar": "Fixed calendar (seasonal climatology)",
    "free": "Free district feed (no leaf-wetness sensor)",
    "node": "AamRakshak node (~Rs.2k, measured leaf wetness)",
    "commercial": "Commercial station (~Rs.40k, clean agromet)",
}

# Measurement-noise budgets per tier (SD). Node uses an accurate digital T/RH
# sensor but a cheaper grid; commercial is cleaner across the board.
_NOISE = {
    "node": {"temp": 0.4, "rh": 2.5, "lw": 1.2},
    "commercial": {"temp": 0.3, "rh": 1.5, "lw": 0.5},
}


def _vec_anthracnose_risk(
    t_max: np.ndarray,
    t_min: np.ndarray,
    rh: np.ndarray,
    lw: np.ndarray,
    sun: np.ndarray,
    wind: np.ndarray,
    coeffs: dict[str, float] = DEFAULT_COEFFS,
) -> np.ndarray:
    """Vectorised form of ``anthracnose_risk`` (identical maths, array inputs)."""
    htr = rh / np.maximum(0.1, t_max - t_min)
    z = (
        coeffs["beta_0"]
        + coeffs["beta_htr"] * htr
        + coeffs["beta_lw"] * lw
        + coeffs["beta_sun"] * sun
        + coeffs["beta_wind"] * wind
    )
    return 1.0 / (1.0 + np.exp(-z))


def tier_risk_scores(panel: pd.DataFrame, tier: str, seed: int) -> np.ndarray:
    """Risk score in [0, 1] for every panel row under one sensor tier."""
    rng = np.random.default_rng(seed)
    n = len(panel)

    if tier == "calendar":
        # Seasonal climatology: mean true infection probability by region+day.
        clim = panel.groupby(["region", "day"])["outbreak_prob"].transform("mean")
        return clim.to_numpy()

    if tier == "free":
        rh = panel["district_rh"].to_numpy()
        lw = np.array([estimate_lw_hours_from_rh(v) for v in rh])
        return _vec_anthracnose_risk(
            panel["district_t_max"].to_numpy(),
            panel["district_t_min"].to_numpy(),
            rh,
            lw,
            panel["district_sunshine"].to_numpy(),
            panel["district_wind"].to_numpy(),
        )

    if tier in ("node", "commercial"):
        nz = _NOISE[tier]
        t_max = panel["t_max"].to_numpy() + rng.normal(0.0, nz["temp"], n)
        t_min = panel["t_min"].to_numpy() + rng.normal(0.0, nz["temp"], n)
        rh = np.clip(panel["rh_morning"].to_numpy() + rng.normal(0.0, nz["rh"], n), 25.0, 100.0)
        lw_true = panel["leaf_wetness_true"].to_numpy()
        lw = np.clip(lw_true + rng.normal(0.0, nz["lw"], n), 0.0, 18.0)
        if tier == "node":
            # Node has no light/wind sensor -> borrow the free district feed.
            sun = panel["district_sunshine"].to_numpy()
            wind = panel["district_wind"].to_numpy()
        else:
            sun = panel["sunshine"].to_numpy() + rng.normal(0.0, 0.4, n)
            wind = panel["wind"].to_numpy() + rng.normal(0.0, 0.3, n)
        return _vec_anthracnose_risk(t_max, t_min, rh, lw, sun, wind)

    raise ValueError(f"unknown tier: {tier!r}")
