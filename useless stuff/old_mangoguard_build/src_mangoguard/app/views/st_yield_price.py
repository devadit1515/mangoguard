"""Yield + Mandi Price page (Plan 6 Task 6)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st


def render(state: dict[str, Any]) -> None:
    st.title("💰 Yield + Mandi Price")
    st.write(
        "Block-level yield and harvest-week mandi-price forecasts. Models "
        "are XGBoost regressors over orchard-health, weather, and "
        "historical AGMARKNET price features."
    )

    artifact_dir = Path("artifacts")
    yield_path = artifact_dir / "yield_xgb_v1.json"
    price_path = artifact_dir / "price_xgb_v1.json"

    if not yield_path.exists() and not price_path.exists():
        st.info(
            "Models not trained yet -- run "
            "`notebooks/06_yield_xgb.ipynb` and "
            "`notebooks/06_price_xgb.ipynb` to fit the XGB models."
        )
        return

    st.subheader("Inputs")
    cols = st.columns(2)
    with cols[0]:
        acreage = st.number_input("Acreage", min_value=0.5, max_value=200.0, value=10.0)
        tree_count = st.number_input("Tree count", min_value=10, max_value=10000, value=250)
        ndvi_int = st.number_input(
            "NDVI integral Apr-Jun", min_value=0.0, max_value=200.0, value=70.0
        )
        gdd = st.number_input("Cumulative GDD>10C", min_value=0.0, max_value=4000.0, value=1500.0)
    with cols[1]:
        rainfall = st.number_input(
            "Total rainfall (mm)", min_value=0.0, max_value=3000.0, value=300.0
        )
        rh = st.number_input("Mean RH%", min_value=0.0, max_value=100.0, value=75.0)
        soil_ph = st.number_input("Soil pH", min_value=4.0, max_value=9.0, value=6.5)
        prev_yield = st.number_input(
            "Previous-season yield (kg/acre)", min_value=0.0, max_value=30000.0, value=8500.0
        )

    if st.button("Predict yield"):
        if not yield_path.exists():
            st.error("Yield model not yet trained.")
        else:
            from mangoguard.yield_price.yield_xgb import (  # noqa: PLC0415
                load_yield_model,
                predict_yield,
            )

            model = load_yield_model(yield_path)
            features = {
                "acreage": float(acreage),
                "tree_count": int(tree_count),
                "mean_tree_age": 12,
                "ndvi_integral_apr_jun": float(ndvi_int),
                "cum_gdd_above_10c": float(gdd),
                "total_rainfall_mm": float(rainfall),
                "mean_rh_pct": float(rh),
                "soil_texture_class": 1.0,
                "soil_ph": float(soil_ph),
                "prev_season_yield_kg_per_acre": float(prev_yield),
                "season_year": 2025,
            }
            predicted = predict_yield(model, features)
            st.metric(
                "Predicted yield (kg/acre)",
                f"{predicted:,.0f}",
                delta=f"vs {prev_yield:,.0f} prev",
            )
