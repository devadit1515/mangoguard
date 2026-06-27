"""Spray-reduction analysis (success condition S4) -- the practical payoff.

Compares the status-quo fixed calendar with the node's early-warning rule on the
same simulated seasons. Status-quo Konkan Alphonso growers spray prophylactically
every ~7-10 days (commonly 10-15 sprays a season -- the documented over-use the
tool targets), so the calendar baseline is an 8-day interval.

Coverage is measured over **true high-infection-pressure days** (latent
infection probability >= 0.5), i.e. "did a spray protect the orchard when
conditions genuinely favoured infection?" -- the question the pre-registered S4
asks. Coverage over every Bernoulli outbreak day is reported too, as a stricter
secondary number, but it unfairly rewards blind spraying because some outbreaks
land on genuinely low-risk days no weather model can foresee.

A day is *protected* if a spray fell within the fungicide's residual window
before it. The headline: cut sprays without losing cover of the dangerous days.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from aamrakshak.riskengine.ppi import (
    spray_schedule_calendar,
    spray_schedule_early_warning,
)

PROTECT_DAYS = 10  # residual protection window of a contact fungicide
CALENDAR_INTERVAL = 8  # status-quo prophylactic spraying (~12 sprays/season)
HIGH_RISK_PROB = 0.5  # latent infection prob marking a high-pressure day


def _coverage(spray_days: list[int], target_days: np.ndarray, protect: int) -> float:
    """Fraction of target days protected by a spray within ``protect`` days before."""
    if len(target_days) == 0:
        return float("nan")
    sd = np.array(sorted(spray_days))
    if sd.size == 0:
        return 0.0
    covered = sum(bool(np.any((sd <= d) & (d - sd <= protect))) for d in target_days)
    return covered / len(target_days)


def _schedules(g: pd.DataFrame, threshold_pct: float) -> tuple[list[int], list[int]]:
    n_days = len(g)
    cal = [e.day for e in spray_schedule_calendar(n_days, CALENDAR_INTERVAL)]
    # sustain_days=1: anthracnose can establish in a single wet day, so a
    # one-day high-risk signal is acted on rather than waited out.
    ew = [
        e.day
        for e in spray_schedule_early_warning(
            g["node_risk_pct"].to_numpy(),
            threshold=threshold_pct,
            sustain_days=1,
            lockout_days=PROTECT_DAYS,
        )
    ]
    return cal, ew


def _block_metrics(g: pd.DataFrame, threshold_pct: float) -> dict:
    g = g.sort_values("day")
    cal, ew = _schedules(g, threshold_pct)
    high_risk_days = g["day"].to_numpy()[g["outbreak_prob"].to_numpy() >= HIGH_RISK_PROB]
    outbreak_days = g["day"].to_numpy()[g["outbreak"].to_numpy() == 1]
    return {
        "cal_sprays": len(cal),
        "ew_sprays": len(ew),
        "cal_cov_hr": _coverage(cal, high_risk_days, PROTECT_DAYS),
        "ew_cov_hr": _coverage(ew, high_risk_days, PROTECT_DAYS),
        "cal_cov_ob": _coverage(cal, outbreak_days, PROTECT_DAYS),
        "ew_cov_ob": _coverage(ew, outbreak_days, PROTECT_DAYS),
    }


def _aggregate(rows: list[dict]) -> dict:
    cal_s = np.array([r["cal_sprays"] for r in rows], float)
    ew_s = np.array([r["ew_sprays"] for r in rows], float)
    return {
        "calendar_sprays_mean": round(float(np.mean(cal_s)), 2),
        "early_warning_sprays_mean": round(float(np.mean(ew_s)), 2),
        "spray_reduction_pct": round(100.0 * (1 - np.mean(ew_s) / np.mean(cal_s)), 1),
        "calendar_coverage_highrisk": round(float(np.nanmean([r["cal_cov_hr"] for r in rows])), 4),
        "early_warning_coverage_highrisk": round(
            float(np.nanmean([r["ew_cov_hr"] for r in rows])), 4
        ),
        "calendar_coverage_outbreaks": round(float(np.nanmean([r["cal_cov_ob"] for r in rows])), 4),
        "early_warning_coverage_outbreaks": round(
            float(np.nanmean([r["ew_cov_ob"] for r in rows])), 4
        ),
    }


def run_spray_reduction(
    panel: pd.DataFrame,
    node_risk_cal: np.ndarray,
    thresholds_pct: list[float] | None = None,
    chosen_threshold_pct: float = 30.0,
) -> dict:
    """Calendar vs early-warning sprays and coverage, overall and per region."""
    thresholds_pct = thresholds_pct or [20.0, 25.0, 30.0, 35.0, 40.0]
    work = panel.copy()
    work["node_risk_pct"] = 100.0 * node_risk_cal
    groups = [g for _, g in work.groupby(["region", "season", "block"], sort=True)]

    sweep = []
    for thr in thresholds_pct:
        agg = _aggregate([_block_metrics(g, thr) for g in groups])
        sweep.append({"threshold_pct": thr, **agg})

    overall = _aggregate([_block_metrics(g, chosen_threshold_pct) for g in groups])

    per_region = {}
    for region, gr in work.groupby("region", sort=True):
        rows = [_block_metrics(g, chosen_threshold_pct) for _, g in gr.groupby(["season", "block"])]
        per_region[region] = _aggregate(rows)

    return {
        "protect_days": PROTECT_DAYS,
        "calendar_interval_days": CALENDAR_INTERVAL,
        "high_risk_prob_threshold": HIGH_RISK_PROB,
        "chosen_threshold_pct": chosen_threshold_pct,
        "overall": overall,
        "per_region": per_region,
        "threshold_sweep": sweep,
    }
