"""Home + connector status (Plan 6 Tasks 1+2)."""

from __future__ import annotations

from typing import Any

import streamlit as st

from mangoguard.schema import ConnectorSource
from mangoguard.store import FeedStore


def render(state: dict[str, Any]) -> None:
    st.title("🥭 MangoGuard")
    st.subheader("Climate- and market-aware spray decisions for Konkan Alphonso")
    st.write(
        "This is an interoperability layer that ingests data from the "
        "monitoring systems your farm already runs (Fyllo, Fasal, Pessl, "
        "IMD, AGMARKNET, CROPSAP, Sentinel-2) and turns them into per-block "
        "per-market spray recommendations."
    )

    st.divider()
    cols = st.columns(2)
    with cols[0]:
        st.subheader("Block selection")
        state["block_id"] = st.text_input(
            "Block ID", value=state.get("block_id", "ratnagiri_block_A")
        )
    with cols[1]:
        st.subheader("Feed store")
        path = st.text_input("Feed store path", value=state.get("feed_store_path", "feeds.db"))
        state["feed_store_path"] = path

    st.divider()
    st.subheader("Connector status")
    try:
        store = FeedStore(state["feed_store_path"])
        counts = store.count_by_source()
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not read feed store at {state['feed_store_path']}: {exc}")
        return
    rows = []
    for src in ConnectorSource:
        rows.append({"connector": src.value, "rows_ingested": int(counts.get(src, 0))})
    st.dataframe(rows, hide_index=True, use_container_width=True)
