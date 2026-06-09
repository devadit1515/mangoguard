"""Spray Recommender page (Plan 6 Task 5) -- FOCAL module UX."""

from __future__ import annotations

from datetime import date
from typing import Any

import streamlit as st

from mangoguard.recommend.markets import MarketSegment
from mangoguard.recommend.recommend import recommend
from mangoguard.store import FeedStore


def render(state: dict[str, Any]) -> None:
    st.title("💊 Spray Recommender")
    st.write(
        "Per-block, per-market spray decisions. The recommender combines "
        "disease-pressure (PPI), CIB&RC pesticide registration, MRL "
        "constraints for the target market, and RASFF rejection history."
    )

    block_id = state.get("block_id", "ratnagiri_block_A")
    cols = st.columns(3)
    with cols[0]:
        decision_day = st.date_input("Decision day", value=date.today())
    with cols[1]:
        market_name = st.selectbox(
            "Target market",
            [m.name for m in MarketSegment],
            index=[m.name for m in MarketSegment].index(
                state.get("target_market", "DOMESTIC_MANDI")
            ),
        )
        state["target_market"] = market_name
    with cols[2]:
        days_until_harvest = st.number_input(
            "Days until harvest",
            min_value=0,
            max_value=365,
            value=int(state.get("days_until_harvest", 45)),
        )
        state["days_until_harvest"] = int(days_until_harvest)

    if not st.button("Generate recommendation"):
        return
    try:
        store = FeedStore(state["feed_store_path"])
    except Exception as exc:  # noqa: BLE001
        st.error(f"Could not open feed store: {exc}")
        return
    result = recommend(
        store,
        block_id=block_id,
        day=decision_day,
        target_market=MarketSegment[market_name],
        days_until_harvest=int(days_until_harvest),
    )

    cols = st.columns(2)
    cols[0].metric("Disease pressure (PPI)", f"{result.ppi:.1f}")
    cols[1].metric("Primary pathogen", result.primary_pathogen)

    if result.pesticide is None:
        st.warning("No spray recommended.")
        st.info(result.rationale)
        return

    st.success(f"**Spray {result.pesticide}** ({result.dose})")
    cols = st.columns(3)
    cols[0].metric("PHI (days)", str(result.phi_days))
    cols[1].metric(
        "Earliest harvest",
        result.harvest_date_constraint.isoformat() if result.harvest_date_constraint else "n/a",
    )
    if result.expected_rasff_rejection_p is not None:
        cols[2].metric("Expected RASFF rejection p", f"{result.expected_rasff_rejection_p:.3f}")
    st.subheader("Rationale")
    st.info(result.rationale)
    if result.alternatives:
        st.subheader("Alternatives")
        st.dataframe([{"alternative": a} for a in result.alternatives], hide_index=True)
