"""Orchard health queries -- NDVI/NDRE/NDMI time-series + anomaly detection.

These functions back the Streamlit "Orchard health" page. They wrap
``FeedStore.query`` with vegetation-index-specific filtering and
deviations-from-rolling-mean anomaly detection.

The dashboard's "absentee owner wants to verify farm health remotely"
use case is the primary driver: a tidy DataFrame ordered oldest-first
that Streamlit can chart in one line; a list of flagged anomalies the
owner can act on.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from mangoguard.store import FeedStore

_DEFAULT_DAYS_BACK = 90
_ROLLING_WINDOW_DAYS = 30
_ANOMALY_SD_THRESHOLD = 1.0
_NDVI_LOWER_BOUND = -1.0
_NDVI_UPPER_BOUND = 1.0
_MIN_DAYS_FOR_ROLLING_STATS = 2


def _utc_window(days_back: int) -> tuple[datetime, datetime]:
    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(days=days_back)
    return start, end


def block_vegetation_timeseries(
    store: FeedStore,
    block_id: str,
    *,
    days_back: int = _DEFAULT_DAYS_BACK,
    end_time: datetime | None = None,
) -> pd.DataFrame:
    """Return ``DataFrame[ts, ndvi, ndre, ndmi]`` for ``block_id`` over the
    last ``days_back`` days, oldest first.

    Rows with all-three indices missing are dropped. Other rows keep
    their NaN cells so the dashboard can show partial coverage.
    """
    if end_time is None:
        start, end = _utc_window(days_back)
    else:
        end = end_time.astimezone(timezone.utc)
        start = end - timedelta(days=days_back)

    rows = store.query(block_id, start, end)
    records = []
    for obs in rows:
        if obs.ndvi is None and obs.ndre is None and obs.ndmi is None:
            continue
        records.append(
            {
                "ts": obs.ts,
                "ndvi": obs.ndvi,
                "ndre": obs.ndre,
                "ndmi": obs.ndmi,
            }
        )
    if not records:
        return pd.DataFrame(columns=["ts", "ndvi", "ndre", "ndmi"])
    return pd.DataFrame(records).sort_values("ts").reset_index(drop=True)


def block_anomalies(
    store: FeedStore,
    block_id: str,
    *,
    index: str = "ndvi",
    days_back: int = _DEFAULT_DAYS_BACK,
    sd_threshold: float = _ANOMALY_SD_THRESHOLD,
    end_time: datetime | None = None,
) -> list[dict]:
    """Detect points >= ``sd_threshold`` SD below the 30-day rolling mean.

    Returns a list of ``{ts, index, value, rolling_mean, rolling_sd,
    deviation_sd}`` dicts. An empty list is returned when there's not
    enough history to compute a rolling SD.
    """
    if index not in ("ndvi", "ndre", "ndmi"):
        msg = f"index must be one of ndvi/ndre/ndmi, got {index!r}"
        raise ValueError(msg)

    df = block_vegetation_timeseries(store, block_id, days_back=days_back, end_time=end_time)
    if df.empty or df[index].dropna().empty:
        return []

    # Set ts as datetime index and resample to daily means so rolling math
    # is over time, not over observation count.
    series = df.set_index("ts")[index].dropna().sort_index()
    if series.empty:
        return []
    daily = series.resample("1D").mean().dropna()
    if len(daily) < _MIN_DAYS_FOR_ROLLING_STATS:
        return []

    rolling_mean = daily.rolling(_ROLLING_WINDOW_DAYS, min_periods=2).mean()
    rolling_sd = daily.rolling(_ROLLING_WINDOW_DAYS, min_periods=2).std()
    deviations = (rolling_mean - daily) / rolling_sd.replace(0.0, float("nan"))

    anomalies: list[dict] = []
    for ts, dev in deviations.items():
        if pd.isna(dev):
            continue
        if dev >= sd_threshold:
            anomalies.append(
                {
                    "ts": ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts,
                    "index": index,
                    "value": float(daily.loc[ts]),
                    "rolling_mean": float(rolling_mean.loc[ts]),
                    "rolling_sd": float(rolling_sd.loc[ts]),
                    "deviation_sd": float(dev),
                }
            )
    return anomalies


def block_latest_indices(
    store: FeedStore,
    block_id: str,
    *,
    days_back: int = 30,
    end_time: datetime | None = None,
) -> dict[str, float | None]:
    """Latest available {ndvi, ndre, ndmi} for the block (most recent per index)."""
    df = block_vegetation_timeseries(store, block_id, days_back=days_back, end_time=end_time)
    if df.empty:
        return {"ndvi": None, "ndre": None, "ndmi": None}
    latest: dict[str, float | None] = {}
    for col in ("ndvi", "ndre", "ndmi"):
        col_series = df.dropna(subset=[col])
        latest[col] = float(col_series[col].iloc[-1]) if not col_series.empty else None
    return latest


def index_in_valid_range(value: float | None) -> bool:
    """Vegetation indices must be in [-1, 1]; useful sanity check for ingestion."""
    if value is None:
        return True
    return _NDVI_LOWER_BOUND <= value <= _NDVI_UPPER_BOUND
