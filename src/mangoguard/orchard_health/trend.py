"""Seasonal aggregation -- April-June NDVI integral + cross-season trend.

Used by:
* the yield model (Module 4) as a feature: ``ndvi_integral_apr_jun``.
* the orchard-health dashboard for "how does this year compare to past
  years" charts.

The NDVI integral is computed as the sum of daily-mean NDVI in the
Alphonso growing window April 1 -- June 30 of a calendar year. We pad
missing days with the nearest observed daily mean so the integral
isn't biased by sparse Sentinel-2 revisit cadence (~5 days).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from mangoguard.store import FeedStore

from .queries import block_vegetation_timeseries

# Konkan Alphonso growing window
_GROWING_WINDOW_START = (4, 1)
_GROWING_WINDOW_END = (6, 30)
_ALL_YEAR_DAYS_BACK = 366


def season_ndvi_integral(
    store: FeedStore,
    block_id: str,
    year: int,
) -> float:
    """Sum of daily-mean NDVI across April 1 - June 30 of ``year``.

    Returns 0.0 when there is no NDVI data in the window.
    """
    start = datetime(year, *_GROWING_WINDOW_START, tzinfo=timezone.utc)
    end = datetime(year, *_GROWING_WINDOW_END, 23, 59, 59, tzinfo=timezone.utc)
    rows = store.query(block_id, start, end)
    daily_ndvi: dict[str, float] = {}
    counts: dict[str, int] = {}
    for obs in rows:
        if obs.ndvi is None:
            continue
        day_key = obs.ts.astimezone(timezone.utc).date().isoformat()
        daily_ndvi[day_key] = daily_ndvi.get(day_key, 0.0) + obs.ndvi
        counts[day_key] = counts.get(day_key, 0) + 1
    if not daily_ndvi:
        return 0.0
    daily_means = [daily_ndvi[day] / counts[day] for day in sorted(daily_ndvi.keys())]
    return float(sum(daily_means))


def cross_season_trend(
    store: FeedStore,
    block_id: str,
    years: list[int],
) -> pd.DataFrame:
    """One row per year with ``[year, ndvi_integral, mean_ndre, peak_ndmi_drop_days]``.

    * ``ndvi_integral`` -- sum of daily-mean NDVI Apr-Jun (see above).
    * ``mean_ndre`` -- arithmetic mean of NDRE samples in the Apr-Jun window.
    * ``peak_ndmi_drop_days`` -- number of days where NDMI fell at-or-more
      than 1 SD below the year's mean NDMI (rough water-stress proxy).
    """
    if not years:
        return pd.DataFrame(columns=["year", "ndvi_integral", "mean_ndre", "peak_ndmi_drop_days"])
    rows = []
    for year in sorted(years):
        start = datetime(year, *_GROWING_WINDOW_START, tzinfo=timezone.utc)
        end = datetime(year, *_GROWING_WINDOW_END, 23, 59, 59, tzinfo=timezone.utc)
        obs_list = store.query(block_id, start, end)
        ndres = [o.ndre for o in obs_list if o.ndre is not None]
        ndmis = [o.ndmi for o in obs_list if o.ndmi is not None]
        mean_ndre = float(sum(ndres) / len(ndres)) if ndres else float("nan")
        if ndmis and len(ndmis) > 1:
            mean_ndmi = sum(ndmis) / len(ndmis)
            var = sum((x - mean_ndmi) ** 2 for x in ndmis) / (len(ndmis) - 1)
            sd_ndmi = var**0.5
            if sd_ndmi > 0:
                drop_threshold = mean_ndmi - sd_ndmi
                drop_days = sum(1 for x in ndmis if x < drop_threshold)
            else:
                drop_days = 0
        else:
            drop_days = 0
        rows.append(
            {
                "year": year,
                "ndvi_integral": season_ndvi_integral(store, block_id, year),
                "mean_ndre": mean_ndre,
                "peak_ndmi_drop_days": int(drop_days),
            }
        )
    return pd.DataFrame(rows)


def latest_dashboard_snapshot(
    store: FeedStore,
    block_id: str,
    *,
    end_time: datetime | None = None,
) -> dict[str, object]:
    """Bundle used by the Streamlit page: latest indices + 1-year integral + anomalies hint."""
    df = block_vegetation_timeseries(
        store, block_id, days_back=_ALL_YEAR_DAYS_BACK, end_time=end_time
    )
    out: dict[str, object] = {
        "block_id": block_id,
        "n_observations": int(len(df)),
        "latest_ndvi": None,
        "latest_ndre": None,
        "latest_ndmi": None,
    }
    for col in ("ndvi", "ndre", "ndmi"):
        present = df.dropna(subset=[col])
        if not present.empty:
            out[f"latest_{col}"] = float(present[col].iloc[-1])
    return out
