"""AamRakshak dashboard: turn a node's readings into a spray decision.

Run:  streamlit run app/streamlit_app.py

Loads an AamRakshak node log (CSV or JSON), recomputes anthracnose infection
risk with the same Akem model the node runs, and shows the current risk band,
the early-warning spray decision, and the season history. Works on the bundled
sample log out of the box; upload your own node export to see your orchard.
"""

from __future__ import annotations

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aamrakshak.io.ingest import readings_from_csv, readings_from_node_json  # noqa: E402
from aamrakshak.riskengine.ppi import (  # noqa: E402
    VARIETY_SUSCEPTIBILITY,
    infection_risk_pct,
    spray_schedule_early_warning,
)

SAMPLE = ROOT / "data" / "sample_node_log.csv"
PROTECT_DAYS = 10

st.set_page_config(page_title="AamRakshak", page_icon="🥭", layout="wide")


def band(pct: float) -> tuple[str, str]:
    if pct >= 25:
        return "HIGH — spray window", "🔴"
    if pct >= 12:
        return "WATCH", "🟠"
    return "LOW — safe", "🟢"


@st.cache_data
def load_readings(raw: bytes | None, name: str):
    if raw is None:
        rows = readings_from_csv(SAMPLE)
    elif name.endswith(".json"):
        rows = readings_from_node_json(raw.decode("utf-8"))
    else:
        tmp = ROOT / "data" / "_uploaded_tmp.csv"
        tmp.write_bytes(raw)
        rows = readings_from_csv(tmp)
    return rows


# ----------------------------------------------------------------- sidebar ---
st.sidebar.title("🥭 AamRakshak")
st.sidebar.caption("Leaf-wetness anthracnose early-warning for mango")
up = st.sidebar.file_uploader("Upload a node log (CSV or JSON)", type=["csv", "json"])
variety = st.sidebar.selectbox("Variety", list(VARIETY_SUSCEPTIBILITY), index=0)
threshold = st.sidebar.slider("Spray threshold (risk %)", 10, 50, 25, 1)
st.sidebar.markdown(
    "Readings come from the ₹2,000 node (SHT31 + DS18B20 + DIY leaf-wetness grid). "
    "Risk is the Akem (2006) humid-thermal-ratio model, computed the same way on the "
    "node and here."
)

raw = up.getvalue() if up is not None else None
name = up.name if up is not None else "sample"
rows = load_readings(raw, name)

df = pd.DataFrame(
    {
        "date": [r.date for r in rows],
        "t_max_c": [r.t_max_c for r in rows],
        "t_min_c": [r.t_min_c for r in rows],
        "rh_morning_pct": [r.rh_morning_pct for r in rows],
        "leaf_wetness_hr": [r.leaf_wetness_hr for r in rows],
    }
)
df["risk_pct"] = [infection_risk_pct(r.to_inputs(), variety=variety) for r in rows]

# ----------------------------------------------------------------- header ----
st.title("Anthracnose early-warning dashboard")
st.caption(
    f"{len(df)} daily readings · variety: {variety.title()} · "
    "source: " + ("uploaded log" if raw else "bundled sample (simulated season)")
)

latest = df.iloc[-1]
label, dot = band(latest["risk_pct"])

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Today's risk", f"{latest['risk_pct']:.0f}%", help="Akem anthracnose infection probability"
)
c2.metric("Status", f"{dot} {label.split(' — ')[0]}")
c3.metric("Leaf wetness", f"{latest['leaf_wetness_hr']:.1f} h")
c4.metric("Morning RH", f"{latest['rh_morning_pct']:.0f}%")

if latest["risk_pct"] >= threshold:
    st.error(
        f"**Spray window open.** Risk {latest['risk_pct']:.0f}% ≥ your {threshold}% threshold. "
        "Conditions favour anthracnose infection — protect now if the last spray was more than "
        f"{PROTECT_DAYS} days ago. Advisory only; follow label dose and pre-harvest interval."
    )
else:
    st.success(
        f"**No spray needed.** Risk {latest['risk_pct']:.0f}% is below your {threshold}% threshold. "
        "Re-check in a day or two."
    )

# ----------------------------------------------------------------- history ---
st.subheader("Season risk history")

events = spray_schedule_early_warning(
    df["risk_pct"].tolist(), threshold=float(threshold), sustain_days=1, lockout_days=PROTECT_DAYS
)
spray_days = {e.day for e in events}
df["spray"] = [i in spray_days for i in range(len(df))]
df["date"] = pd.to_datetime(df["date"], errors="coerce")

base = alt.Chart(df).encode(x=alt.X("date:T", title="date"))
line = base.mark_line(color="#1b7837").encode(
    y=alt.Y("risk_pct:Q", title="infection risk (%)", scale=alt.Scale(domain=[0, 100]))
)
rule = (
    alt.Chart(pd.DataFrame({"y": [threshold]}))
    .mark_rule(strokeDash=[5, 4], color="#888")
    .encode(y="y:Q")
)
sprays = (
    alt.Chart(df[df["spray"]])
    .mark_point(shape="triangle-down", size=120, color="#542788", filled=True)
    .encode(x="date:T", y=alt.Y("risk_pct:Q"))
)
st.altair_chart((line + rule + sprays).properties(height=320), use_container_width=True)

n_sprays = int(df["spray"].sum())
st.caption(
    f"Early-warning rule fired **{n_sprays} sprays** this season (purple ▼), each when risk crossed "
    f"{threshold}% and the orchard was unprotected. A fixed calendar at the same site sprays ~12 times."
)

with st.expander("How the risk is computed (the science)"):
    st.markdown(
        """
The node measures the humid-thermal ratio (morning RH ÷ daily temperature range)
and leaf-wetness hours, then evaluates Akem's (2006) logistic regression for
*Colletotrichum gloeosporioides* infection. Leaf wetness is the decisive input:
in the project's evaluation, adding it lifted ROC-AUC from 0.75 (free district
feed) to 0.86 (node), matching a ₹40,000 commercial station at ~5% of the cost.
Recommendations are advisory; the grower makes the final call and follows the
label dose and pre-harvest interval.
        """
    )

st.subheader("Recent readings")
st.dataframe(
    df[["date", "t_max_c", "t_min_c", "rh_morning_pct", "leaf_wetness_hr", "risk_pct"]].tail(14),
    use_container_width=True,
    hide_index=True,
)
