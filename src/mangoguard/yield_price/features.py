"""Feature engineering for the yield + price models (Plan 5 Task 9).

``build_features`` takes a FeedStore + block metadata and returns a flat
dict suitable for direct use with the XGBoost regressors. Features are
grouped:

* **Block metadata** (acreage, tree count, mean age, soil texture, soil pH).
* **Orchard health** (NDVI integral from ``orchard_health.trend``).
* **Weather aggregates** (cumulative GDD>10 deg-C, total rainfall mm,
  mean RH%, mean Tmax) over the Apr-Jun Konkan growing window.
* **Previous-season yield** (optional; ``None`` for first-season blocks).

Missing values are kept as NaN (XGBoost handles them natively) so we
don't bias predictions with imputation magic.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from mangoguard.orchard_health.trend import season_ndvi_integral
from mangoguard.store import FeedStore

_GROWING_WINDOW_START = (4, 1)
_GROWING_WINDOW_END = (6, 30)
_GDD_BASELINE_C = 10.0


def _safe_mean(values: list[float | None]) -> float | None:
    cleaned = [v for v in values if v is not None]
    return sum(cleaned) / len(cleaned) if cleaned else None


def _cumulative_gdd(t_air_values: list[float | None], baseline_c: float) -> float:
    """Sum of max(0, T - baseline) over the readings -- a simple GDD proxy."""
    total = 0.0
    for t in t_air_values:
        if t is not None and t > baseline_c:
            total += t - baseline_c
    return total


def build_features(
    store: FeedStore,
    block_id: str,
    season_year: int,
    block_meta: dict[str, Any] | None = None,
) -> dict[str, float | int | None]:
    """Build a feature dict for one (block, season) for the yield/price models.

    Args:
        store: Feed store with weather + Sentinel-2 ingestion for the block.
        block_id: Orchard block identifier.
        season_year: Calendar year (Apr 1 - Jun 30 of this year is the window).
        block_meta: Optional metadata dict with keys
            ``{acreage, tree_count, mean_tree_age, soil_texture_class, soil_ph,
              prev_season_yield_kg_per_acre}``. Missing keys -> ``None``.

    Returns:
        Flat dict mapping feature name -> numeric value (or ``None`` for
        missing). The 11 features are:
            acreage, tree_count, mean_tree_age,
            ndvi_integral_apr_jun,
            cum_gdd_above_10c, total_rainfall_mm, mean_rh_pct,
            soil_texture_class, soil_ph,
            prev_season_yield_kg_per_acre,
            season_year
    """
    block_meta = block_meta or {}
    start = datetime(season_year, *_GROWING_WINDOW_START, tzinfo=timezone.utc)
    end = datetime(season_year, *_GROWING_WINDOW_END, 23, 59, 59, tzinfo=timezone.utc)
    rows = store.query(block_id, start, end)

    t_air = [obs.t_air_c for obs in rows]
    rh = [obs.rh_pct for obs in rows]
    precip = [obs.precip_mm for obs in rows]
    total_rainfall = sum(p for p in precip if p is not None) if precip else 0.0

    return {
        "acreage": block_meta.get("acreage"),
        "tree_count": block_meta.get("tree_count"),
        "mean_tree_age": block_meta.get("mean_tree_age"),
        "ndvi_integral_apr_jun": season_ndvi_integral(store, block_id, season_year),
        "cum_gdd_above_10c": _cumulative_gdd(t_air, _GDD_BASELINE_C),
        "total_rainfall_mm": total_rainfall,
        "mean_rh_pct": _safe_mean(rh),
        "soil_texture_class": block_meta.get("soil_texture_class"),
        "soil_ph": block_meta.get("soil_ph"),
        "prev_season_yield_kg_per_acre": block_meta.get("prev_season_yield_kg_per_acre"),
        "season_year": season_year,
    }


FEATURE_NAMES: tuple[str, ...] = (
    "acreage",
    "tree_count",
    "mean_tree_age",
    "ndvi_integral_apr_jun",
    "cum_gdd_above_10c",
    "total_rainfall_mm",
    "mean_rh_pct",
    "soil_texture_class",
    "soil_ph",
    "prev_season_yield_kg_per_acre",
    "season_year",
)
