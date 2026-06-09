"""Orchard Health page (Plan 6 Task 4) -- NDVI/NDRE/NDMI time-series + anomalies."""

from __future__ import annotations

from typing import Any

import streamlit as st

from mangoguard.orchard_health.queries import block_anomalies, block_vegetation_timeseries
from mangoguard.orchard_health.trend import latest_dashboard_snapshot
from mangoguard.store import FeedStore


def render(state: dict[str, Any]) -> None:
    st.title("🌳 Orchard Health")
    block_id = state.get("block_id", "ratnagiri_block_A")
    st.caption(f"Block: **{block_id}**")

    try:
        store = FeedStore(state["feed_store_path"])
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not open feed store: {exc}")
        return

    snapshot = latest_dashboard_snapshot(store, block_id)
    cols = st.columns(3)
    cols[0].metric(
        "Latest NDVI",
        f"{snapshot.get('latest_ndvi'):.3f}" if snapshot.get("latest_ndvi") else "n/a",
    )
    cols[1].metric(
        "Latest NDRE",
        f"{snapshot.get('latest_ndre'):.3f}" if snapshot.get("latest_ndre") else "n/a",
    )
    cols[2].metric(
        "Latest NDMI",
        f"{snapshot.get('latest_ndmi'):.3f}" if snapshot.get("latest_ndmi") else "n/a",
    )
    st.caption(
        f"{snapshot.get('n_observations', 0)} Sentinel-2 observations in the past 12 months."
    )

    st.subheader("Vegetation index time-series (90 days)")
    df = block_vegetation_timeseries(store, block_id, days_back=90)
    if df.empty:
        st.info("No NDVI / NDRE / NDMI observations yet for this block.")
        return
    st.line_chart(df.set_index("ts"))

    st.subheader("Anomalies (>= 1 SD below 30-day rolling mean)")
    anomalies = block_anomalies(store, block_id, index="ndvi", days_back=90)
    if not anomalies:
        st.success("No anomalies detected.")
    else:
        st.dataframe(anomalies, hide_index=True)
