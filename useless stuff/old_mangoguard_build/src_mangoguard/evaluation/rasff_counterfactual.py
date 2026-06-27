"""RASFF counterfactual prevention-rate evaluator.

Per spec section 4.6.3: for each historical RASFF rejection, **replay**
the recommender on the violating (pathogen, destination) pair. The
recommender "prevents" the rejection if it would have picked a different
active ingredient than the one that triggered the historical violation.

For the baseline (ICAR-CISH calendar) we ask the same question: would
the calendar have prescribed the offending AI?

The prevention rate is

    prevention_rate = #{prevented} / #{total rejections}

Spec section 4.6.3 success threshold:

    relative_improvement_pct = 100 * (mg_rate - icar_rate) / icar_rate
    relative_improvement_pct >= 30   (MangoGuard reduces rejections by >=30%)

This is the headline number that goes in CREST report Section 8
(Results) and is the most defensible "creativity that worked" anchor
for criterion 4.3.

Note on assumptions:

* The RASFF CSV is a sample of rejections only -- we don't know what
  was *not* rejected. So the prevention rate is computed only over
  observed rejections. It's an upper bound on the recommender's true
  effect (because a recommender that prevents the rejected AI may
  still suggest another AI that would have failed).
* For MangoGuard we use ``rasff.rejection_probability`` as the proxy:
  an AI is "prevented" when its smoothed probability exceeds the
  recommender's export cutoff (so the recommender would have filtered
  it out). This matches the live-time decision flow in
  ``recommend.recommend()``.
* For ICAR-CISH we ask whether the calendar at the rejection's ISO week
  prescribes the offending AI. If yes -> the baseline would have
  produced that rejection too -> not prevented.
"""

from __future__ import annotations

import pandas as pd

from mangoguard.recommend import rasff as _rasff_module

from .baseline_schedule import all_pesticides_in_schedule, load_baseline

# Default cutoff matches recommend.py ._EXPORT_RASFF_CUTOFF; kept here as a
# module-level constant so notebooks can sweep across cutoff values.
_DEFAULT_RASFF_CUTOFF = 0.20

# spec section 4.6.3
_TARGET_RELATIVE_IMPROVEMENT_PCT = 30.0


def _ai_would_be_filtered_by_mangoguard(
    ai: str,
    destination: str,
    cutoff: float,
) -> bool:
    """Recommender filters the AI when its smoothed historical rejection
    probability against ``destination`` exceeds ``cutoff``.
    """
    p_hat = _rasff_module.rejection_probability(ai, destination)
    return p_hat > cutoff


def _ai_would_be_picked_by_icar_baseline(ai: str, iso_week: int) -> bool:
    """ICAR-CISH baseline would pick ``ai`` if it appears anywhere in its
    schedule for the given ISO week.
    """
    schedule = load_baseline("icar_cish")
    return any(entry.pesticide == ai and entry.covers_week(iso_week) for entry in schedule.entries)


def evaluate_rasff_counterfactual(
    rasff_rejections: pd.DataFrame,
    *,
    cutoff: float = _DEFAULT_RASFF_CUTOFF,
) -> dict[str, float | int]:
    """Compute MangoGuard vs ICAR-CISH prevention rates over the RASFF CSV.

    Args:
        rasff_rejections: Long-format DataFrame with at minimum
            ``[date, active_ingredient, destination]``. The MangoGuard
            module-level RASFF dataset already has these columns -- you
            can pass ``pd.DataFrame([r.__dict__ for r in rasff.all_rows()])``.
        cutoff: RASFF rejection-probability cutoff applied to the
            recommender filter. Defaults to 0.20 per spec 4.3.3c.

    Returns:
        Dict with ``prevention_rate_mangoguard``, ``prevention_rate_icar_baseline``,
        ``relative_improvement_pct``, ``n_rejections``, ``cutoff``.
    """
    if rasff_rejections.empty:
        return {
            "prevention_rate_mangoguard": 0.0,
            "prevention_rate_icar_baseline": 0.0,
            "relative_improvement_pct": 0.0,
            "n_rejections": 0,
            "cutoff": float(cutoff),
        }

    required = {"date", "active_ingredient", "destination"}
    missing = required - set(rasff_rejections.columns)
    if missing:
        msg = f"rasff_rejections missing columns: {missing}"
        raise ValueError(msg)

    df = rasff_rejections.copy()
    df["active_ingredient"] = df["active_ingredient"].astype(str).str.lower()
    df["destination"] = df["destination"].astype(str).str.upper()
    df["iso_week"] = pd.to_datetime(df["date"]).dt.isocalendar().week.astype(int)

    mg_prevented = 0
    icar_prevented = 0
    for _, row in df.iterrows():
        ai = row["active_ingredient"]
        dest = row["destination"]
        iso_week = int(row["iso_week"])
        if _ai_would_be_filtered_by_mangoguard(ai, dest, cutoff=cutoff):
            mg_prevented += 1
        if not _ai_would_be_picked_by_icar_baseline(ai, iso_week):
            # If the calendar doesn't pick the offending AI at that week,
            # the baseline trivially "prevents" the rejection.
            icar_prevented += 1

    n = len(df)
    mg_rate = mg_prevented / n
    icar_rate = icar_prevented / n
    # Guard against div-by-zero when the baseline prevents nothing.
    if icar_rate == 0:
        relative_improvement = 100.0 if mg_rate > 0 else 0.0
    else:
        relative_improvement = 100.0 * (mg_rate - icar_rate) / icar_rate

    return {
        "prevention_rate_mangoguard": float(mg_rate),
        "prevention_rate_icar_baseline": float(icar_rate),
        "relative_improvement_pct": float(relative_improvement),
        "n_rejections": int(n),
        "cutoff": float(cutoff),
    }


def evaluate_with_kvk_baseline(
    rasff_rejections: pd.DataFrame,
    *,
    cutoff: float = _DEFAULT_RASFF_CUTOFF,
) -> dict[str, float | int]:
    """Same as ``evaluate_rasff_counterfactual`` but uses KVK Konkan
    baseline instead of ICAR-CISH.

    The Konkan calendar includes an organic neem-oil round and an extra
    flowering-tail hopper spray, so its prevention profile differs
    from the national CISH baseline.
    """
    if rasff_rejections.empty:
        return {
            "prevention_rate_mangoguard": 0.0,
            "prevention_rate_kvk_baseline": 0.0,
            "relative_improvement_pct": 0.0,
            "n_rejections": 0,
            "cutoff": float(cutoff),
        }
    df = rasff_rejections.copy()
    df["active_ingredient"] = df["active_ingredient"].astype(str).str.lower()
    df["destination"] = df["destination"].astype(str).str.upper()
    df["iso_week"] = pd.to_datetime(df["date"]).dt.isocalendar().week.astype(int)

    # kvk_konkan: an AI is "prevented" if the calendar doesn't pick it for that week
    kvk_schedule_ais = all_pesticides_in_schedule("kvk_konkan")
    kvk_schedule = load_baseline("kvk_konkan")
    mg_prevented = 0
    kvk_prevented = 0
    for _, row in df.iterrows():
        ai = row["active_ingredient"]
        dest = row["destination"]
        iso_week = int(row["iso_week"])
        if _ai_would_be_filtered_by_mangoguard(ai, dest, cutoff=cutoff):
            mg_prevented += 1
        # KVK doesn't pick the offending AI?
        if ai not in kvk_schedule_ais or not any(
            entry.pesticide == ai and entry.covers_week(iso_week) for entry in kvk_schedule.entries
        ):
            kvk_prevented += 1
    n = len(df)
    mg_rate = mg_prevented / n
    kvk_rate = kvk_prevented / n
    if kvk_rate == 0:
        relative_improvement = 100.0 if mg_rate > 0 else 0.0
    else:
        relative_improvement = 100.0 * (mg_rate - kvk_rate) / kvk_rate
    return {
        "prevention_rate_mangoguard": float(mg_rate),
        "prevention_rate_kvk_baseline": float(kvk_rate),
        "relative_improvement_pct": float(relative_improvement),
        "n_rejections": int(n),
        "cutoff": float(cutoff),
    }
