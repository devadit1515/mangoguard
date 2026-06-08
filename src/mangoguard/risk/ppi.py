"""Pest Pressure Index (PPI) combiner.

PPI is the per-block-per-day scalar that drives the recommender's
spray-or-no-spray decision. It folds the three pathogen-risk models
into a single 0-100 score and surfaces the dominant pathogen so the
recommender can pick the right pesticide pathway.

Formula
-------
::

    PPI/100 = w_anth * anthracnose_risk
            + w_pm   * powdery_mildew_risk
            + w_hop  * hopper_risk

Default weights ``{anth: 0.5, pm: 0.3, hop: 0.2}`` reflect Konkan
Alphonso's actual disease incidence (anthracnose dominates because of
monsoon RH; powdery mildew is a flowering-season threat; hopper hits
at panicle initiation). Plan 4 Task 5 recalibrates these against
CROPSAP outbreak labels.

NDRE-anomaly boost
------------------
Sentinel-2 NDRE captures chlorophyll/N status. A drop more than 1 SD
below the 30-day rolling mean indicates a stressed canopy, which the
agronomy literature ties to higher anthracnose susceptibility. When
detected, we add ``+0.15`` to the anthracnose component (capped at
1.0) before the weighted sum.

I/O contract
------------
This module READS the FeedStore. It aggregates the 7-day window
``[day - 7, day + 1)`` for weather signals and the 30-day window for
the NDRE baseline. It does not write back to the store.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta, timezone
from typing import TYPE_CHECKING

from mangoguard.risk.anthracnose import AnthracnoseInputs, anthracnose_risk
from mangoguard.risk.hopper import hopper_risk
from mangoguard.risk.powdery_mildew import PowderyMildewInputs, powdery_mildew_risk
from mangoguard.schema import BlockObservation, ConnectorSource

if TYPE_CHECKING:
    from mangoguard.store import FeedStore

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS: dict[str, float] = {"anth": 0.5, "pm": 0.3, "hop": 0.2}

# NDRE-anomaly trigger -- 1 SD below 30-day mean.
NDRE_ANOMALY_SIGMA: float = 1.0
NDRE_ANOMALY_BOOST: float = 0.15

# Aggregation windows.
_WEATHER_WINDOW_DAYS = 7
_NDRE_BASELINE_DAYS = 30

# Numerical constants.
_WEIGHT_SUM_TOLERANCE = 1e-6
_MIN_HISTORY_FOR_SD = 2  # need >=2 samples to estimate population SD
_SOLAR_W_M2_PER_SUN_HOUR = 200.0  # rough threshold: 200 W/m^2 = "sunny hour"


def _day_window_utc(day: date) -> tuple[datetime, datetime]:
    """``[day - 7, day + 1)`` window in UTC for weather aggregation."""
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=timezone.utc)
    start = end - timedelta(days=_WEATHER_WINDOW_DAYS + 1)
    return start, end


def _ndre_baseline_window_utc(day: date) -> tuple[datetime, datetime]:
    """30-day window ending at ``day`` for NDRE rolling-mean baseline."""
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=timezone.utc)
    start = end - timedelta(days=_NDRE_BASELINE_DAYS)
    return start, end


def _safe_mean(values: list[float | None]) -> float | None:
    clean = [v for v in values if v is not None]
    return sum(clean) / len(clean) if clean else None


def _safe_max(values: list[float | None]) -> float | None:
    clean = [v for v in values if v is not None]
    return max(clean) if clean else None


def _safe_min(values: list[float | None]) -> float | None:
    clean = [v for v in values if v is not None]
    return min(clean) if clean else None


def _safe_sum(values: list[float | None]) -> float | None:
    clean = [v for v in values if v is not None]
    return sum(clean) if clean else None


def _stddev(values: list[float]) -> float:
    n = len(values)
    if n < _MIN_HISTORY_FOR_SD:
        return 0.0
    mu = sum(values) / n
    return (sum((v - mu) ** 2 for v in values) / n) ** 0.5


def _cropsap_pressure_for_block(
    obs: list[BlockObservation],
    block_id: str,
) -> float:
    """Average hopper-pressure for the block's taluka from CROPSAP rows.

    CROPSAP rows are keyed by ``{taluka}_{pathogen_slug}`` (see the
    connector's collision-suffix scheme). The block's taluka is the
    prefix before the first underscore in the block_id, falling back
    to the block_id itself when no underscore is present.
    """
    taluka = block_id.split("_", 1)[0] if "_" in block_id else block_id
    hopper_prefix = f"{taluka}_hopper"
    pressures: list[float] = []
    for o in obs:
        if o.source != ConnectorSource.CROPSAP:
            continue
        if not o.block_id.startswith(hopper_prefix):
            continue
        if o.cropsap_pest_pressure is not None:
            pressures.append(o.cropsap_pest_pressure)
    return sum(pressures) / len(pressures) if pressures else 0.0


def compute_ppi(
    store: FeedStore,
    block_id: str,
    day: date,
    weights: dict[str, float] | None = None,
) -> dict[str, float | bool]:
    """Per-block-per-day Pest Pressure Index in [0, 100].

    Parameters
    ----------
    store
        FeedStore to query for weather, NDRE, and CROPSAP observations.
    block_id
        Block to score.
    day
        Calendar day (UTC) for which to compute the score.
    weights
        Optional override of ``{anth, pm, hop}`` weights. Defaults to
        ``DEFAULT_WEIGHTS``. A warning is logged if they don't sum to 1.

    Returns
    -------
    dict with keys: ``ppi`` (0-100), ``anth`` / ``pm`` / ``hop`` (each
    0-1 -- the underlying component scores AFTER any NDRE boost),
    ``ndre_anomaly`` (bool).
    """
    weights = weights if weights is not None else DEFAULT_WEIGHTS
    w_sum = weights["anth"] + weights["pm"] + weights["hop"]
    if abs(w_sum - 1.0) > _WEIGHT_SUM_TOLERANCE:
        logger.warning(
            "compute_ppi: weights %s sum to %.4f, not 1.0 -- proceeding anyway",
            weights,
            w_sum,
        )

    weather_start, weather_end = _day_window_utc(day)
    block_obs = store.query(block_id=block_id, ts_start=weather_start, ts_end=weather_end)

    t_max = _safe_max([o.t_air_c for o in block_obs])
    t_min = _safe_min([o.t_air_c for o in block_obs])
    rh_mean = _safe_mean([o.rh_pct for o in block_obs])
    leaf_wet_sum = _safe_sum([o.leaf_wetness_hr for o in block_obs])
    wind_mean = _safe_mean([o.wind_speed_ms for o in block_obs])
    sunshine = _safe_sum([o.solar_w_m2 for o in block_obs])

    # Fall back to neutral defaults when the window has no weather signal.
    t_max_c = t_max if t_max is not None else 28.0
    t_min_c = t_min if t_min is not None else 22.0
    rh = rh_mean if rh_mean is not None else 70.0
    leaf_wet_hr = leaf_wet_sum if leaf_wet_sum is not None else 0.0
    wind = wind_mean if wind_mean is not None else 2.0
    # Solar->sunshine-hours proxy: rough threshold of 200 W/m^2 = "sunny hour".
    sun_hr = (sunshine / _SOLAR_W_M2_PER_SUN_HOUR) if sunshine is not None else 4.0

    anth_score = anthracnose_risk(
        AnthracnoseInputs(
            t_max_c=t_max_c,
            t_min_c=t_min_c,
            rh_morning_pct=rh,
            leaf_wetness_hr=leaf_wet_hr,
            sunshine_hr=sun_hr,
            wind_speed_ms=wind,
        )
    )
    pm_score = powdery_mildew_risk(PowderyMildewInputs(t_max_c=t_max_c, t_min_c=t_min_c, rh_pct=rh))

    cropsap_obs = store.query_by_source(ConnectorSource.CROPSAP)
    cropsap_obs_windowed = [o for o in cropsap_obs if weather_start <= o.ts < weather_end]
    cropsap_pressure = _cropsap_pressure_for_block(cropsap_obs_windowed, block_id)
    hop_score = hopper_risk(cropsap_pressure, (t_max_c + t_min_c) / 2.0)

    # NDRE anomaly check
    ndre_baseline_start, ndre_baseline_end = _ndre_baseline_window_utc(day)
    ndre_baseline_obs = store.query(
        block_id=block_id, ts_start=ndre_baseline_start, ts_end=ndre_baseline_end
    )
    ndre_history = [
        o.ndre
        for o in ndre_baseline_obs
        if o.source == ConnectorSource.SENTINEL2 and o.ndre is not None
    ]
    ndre_current_candidates = [
        o.ndre for o in block_obs if o.source == ConnectorSource.SENTINEL2 and o.ndre is not None
    ]
    ndre_current = ndre_current_candidates[-1] if ndre_current_candidates else None

    ndre_anomaly = False
    if ndre_current is not None and len(ndre_history) >= _MIN_HISTORY_FOR_SD:
        baseline_mean = sum(ndre_history) / len(ndre_history)
        baseline_sd = _stddev(ndre_history)
        if baseline_sd > 0 and ndre_current < baseline_mean - NDRE_ANOMALY_SIGMA * baseline_sd:
            ndre_anomaly = True
            anth_score = min(1.0, anth_score + NDRE_ANOMALY_BOOST)

    ppi = (
        weights["anth"] * anth_score + weights["pm"] * pm_score + weights["hop"] * hop_score
    ) * 100.0

    return {
        "ppi": ppi,
        "anth": anth_score,
        "pm": pm_score,
        "hop": hop_score,
        "ndre_anomaly": ndre_anomaly,
    }


def primary_pathogen(components: dict[str, float | bool]) -> str:
    """Return the name of the highest-scoring pathogen component.

    Used by the recommender (Plan 4 Task 12) to pick the right pesticide
    pathway. Ties resolve in favor of anthracnose then powdery mildew
    then hopper (matches Konkan disease prevalence).
    """
    scores = {
        "anthracnose": float(components.get("anth", 0.0)),
        "powdery_mildew": float(components.get("pm", 0.0)),
        "hopper": float(components.get("hop", 0.0)),
    }
    priority = {"anthracnose": 0, "powdery_mildew": 1, "hopper": 2}
    return max(scores.items(), key=lambda kv: (kv[1], -priority[kv[0]]))[0]


__all__ = [
    "DEFAULT_WEIGHTS",
    "NDRE_ANOMALY_BOOST",
    "NDRE_ANOMALY_SIGMA",
    "compute_ppi",
    "primary_pathogen",
]
