"""Generate the six required figures for the CREST report.

Run::

    python scripts/make_report_figures.py

Writes PNGs to ``artifacts/figs/``. Every data block below is tagged
``# MOCK`` -- replace these with the real arrays returned by
``evaluation/retrospective.py``, ``evaluation/rasff_counterfactual.py``,
and the orchard-health queries, then re-run this exact script to refresh
all figures. The plotting code does not change between mock and real data.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless backend; no display needed
import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

FIGS = Path(__file__).resolve().parents[1] / "artifacts" / "figs"
FIGS.mkdir(parents=True, exist_ok=True)

# Consistent, print-friendly style.
plt.rcParams.update(
    {
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "font.size": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
    }
)
_GREEN = "#2e7d32"
_AMBER = "#ef6c00"
_GREY = "#9e9e9e"


def _save(fig: plt.Figure, name: str) -> None:
    path = FIGS / name
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print("wrote", path)


def fig1_architecture() -> None:
    """Figure 1 -- system architecture block diagram."""
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.axis("off")

    def box(x, y, w, h, text, color):
        ax.add_patch(
            mpatches.FancyBboxPatch(
                (x, y), w, h, boxstyle="round,pad=0.02", fc=color, ec="black", alpha=0.85
            )
        )
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9, wrap=True)

    sources = [
        "Pessl\n(REST)",
        "IMD\n(REST)",
        "Fyllo\n(scrape)",
        "Fasal\n(scrape)",
        "Plantix\n(OCR)",
        "AGMARKNET",
        "CROPSAP",
        "Sentinel-2",
        "CSV\nfallback",
    ]
    for i, s in enumerate(sources):
        box(0.3 + i * 1.0, 7.4, 0.85, 0.7, s, "#e3f2fd")
    box(0.3, 6.4, 9.55, 0.55, "Connector layer  →  list[BlockObservation]  (one schema)", "#bbdefb")
    box(4.0, 5.3, 2.0, 0.6, "FeedStore\n(SQLite)", "#fff9c4")
    modules = [
        "Risk engine\n(PPI)",
        "Orchard\nhealth",
        "RECOMMENDER\n(focal)",
        "Yield/Price",
        "Chatbot\n(RAG)",
    ]
    for i, m in enumerate(modules):
        color = _AMBER if "RECOMMEND" in m else "#c8e6c9"
        box(0.3 + i * 1.95, 4.0, 1.7, 0.75, m, color)
    box(
        0.3,
        2.9,
        9.55,
        0.6,
        "Streamlit dashboard (6 pages) + Disease detector + Evaluation harness",
        "#d1c4e9",
    )

    # arrows
    ax.annotate("", xy=(5.0, 6.4), xytext=(5.0, 6.2), arrowprops=dict(arrowstyle="-"))
    ax.annotate("", xy=(5.0, 5.9), xytext=(5.0, 6.4), arrowprops=dict(arrowstyle="->"))
    ax.annotate("", xy=(5.0, 4.75), xytext=(5.0, 5.3), arrowprops=dict(arrowstyle="->"))
    ax.annotate("", xy=(5.0, 3.5), xytext=(5.0, 4.0), arrowprops=dict(arrowstyle="->"))
    ax.set_xlim(0, 10)
    ax.set_ylim(2.5, 8.3)
    ax.set_title("MangoGuard system architecture", fontsize=12, fontweight="bold")
    _save(fig, "fig1_architecture.png")


def fig2_roc() -> None:
    """Figure 2 -- ROC curves for PPI vs baselines. MOCK data."""

    # MOCK: replace with real (fpr, tpr) from evaluation/retrospective.py
    def synth_roc(auc_target, n=200):
        x = np.linspace(0, 1, n)
        # power-curve whose AUC approximates the target
        gamma = (1 - auc_target) / auc_target
        y = x**gamma
        return x, y

    fig, ax = plt.subplots(figsize=(6, 6))
    for auc, color, label in [
        (0.86, _GREEN, "MangoGuard PPI (AUC 0.86)"),
        (0.67, _AMBER, "ICAR-CISH calendar (AUC 0.67)"),
        (0.61, _GREY, "Seasonal-mean baseline (AUC 0.61)"),
    ]:
        x, y = synth_roc(auc)
        ax.plot(x, y, color=color, lw=2, label=label)
    ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.5, label="Chance (AUC 0.50)")
    ax.set_xlabel("False-positive rate")
    ax.set_ylabel("True-positive rate")
    ax.set_title("Disease-pressure discrimination (ROC) — MOCK", fontsize=11, fontweight="bold")
    ax.legend(loc="lower right", fontsize=9)
    _save(fig, "fig2_roc_ppi.png")


def fig3_indices() -> None:
    """Figure 3 -- NDVI/NDRE/NDMI seasonal time-series. MOCK data."""
    # MOCK: replace with orchard_health.queries.block_vegetation_timeseries
    rng = np.random.default_rng(11)  # fixed seed -> reproducible mock
    weeks = np.arange(0, 26)
    ndvi = 0.72 + 0.05 * np.sin(weeks / 4) + rng.normal(0, 0.01, weeks.size)
    ndre = 0.50 + 0.04 * np.sin(weeks / 4 - 0.5) + rng.normal(0, 0.01, weeks.size)
    ndmi = 0.30 + 0.06 * np.sin(weeks / 5 - 1.0) + rng.normal(0, 0.015, weeks.size)
    ndre[18:21] -= 0.06  # a stress anomaly window

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(weeks, ndvi, color=_GREEN, lw=2, label="NDVI")
    ax.plot(weeks, ndre, color=_AMBER, lw=2, label="NDRE")
    ax.plot(weeks, ndmi, color="#1565c0", lw=2, label="NDMI")
    ax.axvspan(18, 21, color="red", alpha=0.12)
    ax.text(19.5, 0.66, "NDRE\nanomaly", ha="center", fontsize=8, color="red")
    ax.set_xlabel("Weeks into season (Jan → harvest)")
    ax.set_ylabel("Index value")
    ax.set_title("Pilot-block vegetation indices — MOCK", fontsize=11, fontweight="bold")
    ax.legend(loc="upper right", fontsize=9)
    _save(fig, "fig3_vegetation_indices.png")


def fig4_prevention() -> None:
    """Figure 4 -- RASFF counterfactual prevention rate. MOCK data."""
    # MOCK: replace with evaluation/rasff_counterfactual.py output
    labels = ["MangoGuard\nrecommender", "ICAR-CISH\ncalendar", "KVK Konkan\ncalendar"]
    rates = [0.78, 0.55, 0.58]
    colors = [_GREEN, _AMBER, _GREY]
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    bars = ax.bar(labels, rates, color=colors, alpha=0.9)
    for b, r in zip(bars, rates, strict=False):
        ax.text(b.get_x() + b.get_width() / 2, r + 0.01, f"{r:.0%}", ha="center", fontsize=10)
    ax.set_ylabel("Rejections prevented (rate)")
    ax.set_ylim(0, 1.0)
    ax.set_title("RASFF counterfactual prevention rate — MOCK", fontsize=11, fontweight="bold")
    ax.annotate(
        "+41.8% rel.\nimprovement",
        xy=(0, 0.78),
        xytext=(0.6, 0.92),
        fontsize=9,
        color=_GREEN,
        arrowprops=dict(arrowstyle="->", color=_GREEN),
    )
    _save(fig, "fig4_prevention_rate.png")


def fig5_tier() -> None:
    """Figure 5 -- AUC vs number of integrated systems. MOCK data."""
    # MOCK: replace with the tier ablation from notebook 05
    n_systems = [3, 4, 5]
    auc = [0.71, 0.83, 0.89]
    tier_labels = ["Free feeds\nonly", "+ 1 commercial", "Multi-system\nfusion"]
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.plot(n_systems, auc, "o-", color=_GREEN, lw=2, ms=9)
    for x, y, t in zip(n_systems, auc, tier_labels, strict=False):
        ax.text(x, y + 0.008, f"{y:.2f}", ha="center", fontsize=10)
        ax.text(x, 0.685, t, ha="center", fontsize=8, color=_GREY)
    ax.set_xlabel("Number of integrated monitoring systems")
    ax.set_ylabel("Disease-risk ROC-AUC")
    ax.set_ylim(0.66, 0.93)
    ax.set_xticks(n_systems)
    ax.set_title("Accuracy scales with integration (S1) — MOCK", fontsize=11, fontweight="bold")
    _save(fig, "fig5_connector_tier_auc.png")


def fig6_decision_flow() -> None:
    """Figure 6 -- recommender decision-flow diagram."""
    fig, ax = plt.subplots(figsize=(5.5, 8))
    ax.axis("off")
    steps = [
        ("1. Compute PPI", "#fff9c4"),
        ("PPI ≥ 50?  (else → no-spray)", "#ffe0b2"),
        ("2. Primary pathogen", "#fff9c4"),
        ("3. CIB&RC registered AIs", "#fff9c4"),
        ("4. Filter: PHI ≤ harvest window", "#ffcdd2"),
        ("5. Filter: MRL compliant for market", "#ffcdd2"),
        ("6. Filter: RASFF p̂ ≤ 0.20  (export only)", "#ffcdd2"),
        ("7. Rank: log-eff − log-half-life − log-cost", "#c8e6c9"),
        ("8. Top pick + 3 alternatives + rationale", "#a5d6a7"),
    ]
    y = 7.3
    for i, (text, color) in enumerate(steps):
        ax.add_patch(
            mpatches.FancyBboxPatch(
                (0.4, y), 4.6, 0.55, boxstyle="round,pad=0.02", fc=color, ec="black", alpha=0.9
            )
        )
        ax.text(2.7, y + 0.27, text, ha="center", va="center", fontsize=9)
        if i < len(steps) - 1:  # no arrow after the final box
            ax.annotate(
                "", xy=(2.7, y - 0.02), xytext=(2.7, y - 0.22), arrowprops=dict(arrowstyle="<-")
            )
        y -= 0.82
    ax.set_xlim(0, 5.4)
    ax.set_ylim(0, 8)
    ax.set_title("Recommender decision flow", fontsize=12, fontweight="bold")
    _save(fig, "fig6_recommender_flow.png")


def main() -> None:
    fig1_architecture()
    fig2_roc()
    fig3_indices()
    fig4_prevention()
    fig5_tier()
    fig6_decision_flow()
    print("\nAll 6 figures written to", FIGS)


if __name__ == "__main__":
    main()
