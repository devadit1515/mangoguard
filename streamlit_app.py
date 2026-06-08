"""MangoGuard — Streamlit entry-point (placeholder).

This file is the deploy-time entrypoint for both Streamlit Community Cloud and
Hugging Face Spaces. The real multipage dashboard is implemented in
`src/mangoguard/dashboard/` per Plan 6; until that lands, this placeholder
demonstrates the deployment pipeline works end-to-end and exposes the foundation
data types (BlockObservation schema, FeedStore, Connector ABC) for inspection.
"""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from mangoguard import __version__
from mangoguard.schema import BlockObservation, ConnectorSource

st.set_page_config(
    page_title="MangoGuard",
    page_icon="🥭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🥭 MangoGuard")
st.caption(
    "AI orchard-management & MRL-aware spray-audit system for "
    "mid-sized Indian Alphonso mango growers."
)

st.markdown(
    f"""
**Status:** v{__version__} — foundation only.

This is the deployment placeholder. The real multipage dashboard ships with Plan 6
(Disease Detector, Orchard Health, Spray Recommender, Yield & Price, AskHapus).

Until then, this page demonstrates the deployment pipeline and exercises the
foundation types so you can confirm the build succeeded.
"""
)

st.divider()

st.subheader("Foundation status")
st.markdown(
    """
| Plan | Module | Status |
|------|--------|--------|
| 1 | Repo scaffolding + Connector ABC + BlockObservation + FeedStore | ✅ in progress |
| 2 | Free public baseline connectors (AGMARKNET, IMD, DBSKKV, CROPSAP, Sentinel-2) | pending |
| 3 | Commercial connectors (Pessl, Fyllo, Fasal, Plantix, CSV fallback) | pending |
| 4 | **FOCAL** — disease-risk + market-conditioned MRL recommender | pending |
| 5 | Disease detector + orchard-health + yield/price + chatbot | pending |
| 6 | Streamlit integration + field-validation + report scaffolding | pending |
"""
)

st.divider()

st.subheader("Live schema demo")
st.write(
    "Construct a `BlockObservation` to verify the foundation types are importable "
    "in the deployed environment:"
)

col1, col2 = st.columns(2)
with col1:
    block_id = st.text_input("Block ID", value="B3", max_chars=32)
    source = st.selectbox(
        "Source",
        options=list(ConnectorSource),
        format_func=lambda s: s.value,
    )
with col2:
    t_air_c = st.slider("Air temperature (°C)", min_value=-10.0, max_value=50.0, value=28.4)
    rh_pct = st.slider("Relative humidity (%)", min_value=0.0, max_value=100.0, value=87.2)

obs = BlockObservation(
    block_id=block_id,
    ts=datetime(2026, 7, 12, 10, 30, tzinfo=timezone.utc),
    source=source,
    t_air_c=t_air_c,
    rh_pct=rh_pct,
)
st.code(obs.model_dump_json(indent=2), language="json")

st.divider()

st.subheader("Where to read")
REPO_URL = "https://github.com/devadit1515/mangoguard"
st.markdown(
    f"""
- **GitHub repo:** [devadit1515/mangoguard]({REPO_URL}) (private during build)
- **Design spec:** `docs/superpowers/specs/2026-05-30-mangoguard-design.md`
- **Implementation plans:** `docs/superpowers/plans/00-INDEX.md`
- **Project memory:** `CLAUDE.md`
"""
)
