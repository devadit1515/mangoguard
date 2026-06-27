"""Render every report figure from artifacts/eval_metrics.json (300 DPI PNG).

Run after the evaluation:
    python scripts/run_evaluation.py
    python scripts/make_figures.py

Most figures read only the metrics JSON, so they can never drift from the
reported numbers. The two schematic figures (architecture, hardware) are drawn
here; the one illustrative season trace is recomputed deterministically from the
seeded simulation and is labelled as illustrative.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
FIGS = ROOT / "artifacts" / "figs"
FIGS.mkdir(parents=True, exist_ok=True)

M = json.loads((ROOT / "artifacts" / "eval_metrics.json").read_text(encoding="utf-8"))

# Muted, print-friendly palette.
C_NODE = "#1b7837"
C_FREE = "#d6604d"
C_COMM = "#4393c3"
C_CAL = "#999999"
C_ACCENT = "#542788"
plt.rcParams.update(
    {
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linewidth": 0.5,
    }
)


def save(fig, name: str):
    fig.tight_layout()
    fig.savefig(FIGS / name, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {name}")


# ---------------------------------------------------------- fig 1: pipeline ---
def fig_architecture():
    fig, ax = plt.subplots(figsize=(9, 3.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")

    def box(x, y, w, h, text, color):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.08",
                linewidth=1.2,
                edgecolor="#333333",
                facecolor=color,
                alpha=0.85,
            )
        )
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8.5)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(
            FancyArrowPatch(
                (x1, y1),
                (x2, y2),
                arrowstyle="-|>",
                mutation_scale=12,
                linewidth=1.1,
                color="#333333",
            )
        )

    box(0.1, 1.3, 2.1, 1.4, "Sensors\nSHT31 (T/RH)\nDS18B20 (leaf T)\nleaf-wetness grid", "#c7e9c0")
    box(2.7, 1.3, 2.0, 1.4, "ESP32 edge\nAkem HTR model\non-device", "#fdd0a2")
    box(5.2, 2.2, 2.1, 1.2, "OLED\nrisk band\n(offline)", "#deebf7")
    box(5.2, 0.3, 2.1, 1.2, "Flash log + WiFi\nJSON / CSV", "#deebf7")
    box(7.8, 1.3, 2.0, 1.4, "Dashboard\nrisk history\nspray decision", "#dadaeb")
    for x1, y1, x2, y2 in [
        (2.2, 2.0, 2.7, 2.0),
        (4.7, 2.0, 5.2, 2.8),
        (4.7, 2.0, 5.2, 0.9),
        (7.3, 2.8, 7.8, 2.1),
        (7.3, 0.9, 7.8, 1.9),
    ]:
        arrow(x1, y1, x2, y2)
    ax.set_title("AamRakshak data flow: sense → edge risk → act", fontsize=10)
    save(fig, "fig01_architecture.png")


# ------------------------------------------------------- fig 2: hardware blk ---
def fig_hardware():
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")

    def box(x, y, w, h, text, color="#eeeeee"):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.06",
                linewidth=1.1,
                edgecolor="#333",
                facecolor=color,
            )
        )
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8)

    box(3.6, 2.0, 2.8, 1.2, "ESP32 DevKit\n(MCU + ADC + WiFi)", "#fdd0a2")
    box(0.2, 3.6, 2.4, 0.9, "SHT31  T/RH  (I2C)", "#c7e9c0")
    box(0.2, 2.3, 2.4, 0.9, "DS18B20 leaf T (1-Wire)", "#c7e9c0")
    box(0.2, 1.0, 2.4, 0.9, "Leaf-wetness grid (ADC34)", "#c7e9c0")
    box(7.4, 3.6, 2.4, 0.9, "SSD1306 OLED (I2C)", "#deebf7")
    box(7.4, 2.3, 2.4, 0.9, "LittleFS flash log", "#deebf7")
    box(3.6, 0.4, 2.8, 0.9, "TP4056 + 18650 + 6V solar", "#fee0b6")

    def line(x1, y1, x2, y2):
        ax.plot([x1, x2], [y1, y2], color="#555", linewidth=1.0)

    line(2.6, 4.05, 3.6, 2.9)
    line(2.6, 2.75, 3.6, 2.6)
    line(2.6, 1.45, 3.6, 2.3)
    line(6.4, 2.9, 7.4, 4.05)
    line(6.4, 2.6, 7.4, 2.75)
    line(5.0, 2.0, 5.0, 1.3)
    ax.set_title("Node hardware block diagram (~Rs.1,900, off-the-shelf)", fontsize=10)
    save(fig, "fig02_hardware.png")


# ----------------------------------------------------------- fig 3: ROC tiers -
def fig_roc():
    rc = M["tier_study"]["roc_curves"]
    fig, ax = plt.subplots(figsize=(5.2, 5.0))
    order = [("commercial", C_COMM), ("node", C_NODE), ("free", C_FREE), ("calendar", C_CAL)]
    labels = {
        "commercial": "Commercial station",
        "node": "AamRakshak node",
        "free": "Free district feed",
        "calendar": "Calendar (climatology)",
    }
    for tier, color in order:
        d = rc[tier]
        ax.plot(
            d["fpr"],
            d["tpr"],
            color=color,
            linewidth=1.8,
            label=f"{labels[tier]} (AUC {d['auc']:.3f})",
        )
    ax.plot([0, 1], [0, 1], "--", color="#bbbbbb", linewidth=1, label="chance (0.50)")
    ax.set_xlabel("False-positive rate")
    ax.set_ylabel("True-positive rate")
    ax.set_title("Disease-risk discrimination by data tier")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_aspect("equal")
    save(fig, "fig03_roc_tiers.png")


# ------------------------------------------------------- fig 4: AUC bar chart -
def fig_auc_bars():
    t = M["tier_study"]["tiers"]
    keys = ["calendar", "free", "node", "commercial"]
    names = ["Calendar\n(₹0)", "Free feed\n(₹0)", "AamRakshak\n(~₹2,000)", "Commercial\n(~₹40,000)"]
    vals = [t[k]["auc_mean"] for k in keys]
    errs = [t[k]["auc_sd"] for k in keys]
    colors = [C_CAL, C_FREE, C_NODE, C_COMM]
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    bars = ax.bar(names, vals, yerr=errs, capsize=4, color=colors, alpha=0.9)
    for b, v in zip(bars, vals, strict=True):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.012, f"{v:.3f}", ha="center", fontsize=9)
    ax.axhline(0.5, ls="--", color="#bbb", lw=1)
    ax.set_ylim(0.4, 0.95)
    ax.set_ylabel("ROC-AUC (12-seed mean ± SD)")
    ax.set_title("Leaf wetness is the jump: free feed → node")
    # annotate the gap
    ax.annotate(
        "",
        xy=(2, vals[2]),
        xytext=(1, vals[1]),
        arrowprops=dict(arrowstyle="<->", color=C_ACCENT, lw=1.4),
    )
    ax.text(
        1.5,
        (vals[1] + vals[2]) / 2 + 0.02,
        f"+{vals[2] - vals[1]:.02f} AUC\n(measured\nleaf wetness)",
        ha="center",
        color=C_ACCENT,
        fontsize=8,
    )
    save(fig, "fig04_auc_by_tier.png")


# ---------------------------------------------------------- fig 5: ablation ---
def fig_ablation():
    drops = M["ablation"]["auc_drop_when_removed"]
    labels = {
        "leaf_wetness": "leaf wetness",
        "humidity": "humidity",
        "temp_range": "temp range",
        "sunshine": "sunshine",
        "wind": "wind",
    }
    items = sorted(drops.items(), key=lambda kv: kv[1], reverse=True)
    names = [labels[k] for k, _ in items]
    vals = [v for _, v in items]
    colors = [C_NODE if k == "leaf_wetness" else "#cccccc" for k, _ in items]
    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    bars = ax.barh(names[::-1], vals[::-1], color=colors[::-1])
    for b, v in zip(bars, vals[::-1], strict=True):
        ax.text(v + 0.0015, b.get_y() + b.get_height() / 2, f"{v:.3f}", va="center", fontsize=8)
    ax.set_xlabel("Drop in node ROC-AUC when the feature is removed")
    ax.set_title("Which signal carries the prediction? (leave-one-out)")
    save(fig, "fig05_ablation.png")


# ------------------------------------------------------- fig 6: calibration ---
def fig_calibration():
    rel = M["calibration"]["reliability"]
    fig, ax = plt.subplots(figsize=(5.0, 5.0))
    ax.plot([0, 1], [0, 1], "--", color="#bbb", lw=1, label="perfect calibration")
    for key, color, lab in [
        ("raw", C_FREE, "raw Akem score"),
        ("calibrated", C_NODE, "after Platt scaling"),
    ]:
        pred = [p for p in rel[key]["pred"] if p is not None]
        obs = [o for o in rel[key]["obs"] if o is not None]
        ax.plot(pred, obs, "o-", color=color, lw=1.6, ms=4, label=lab)
    br = M["calibration"]["brier_raw_test"]
    bc = M["calibration"]["brier_calibrated_test"]
    ax.set_xlabel("Predicted infection probability")
    ax.set_ylabel("Observed outbreak frequency")
    ax.set_title(f"Node calibration (Brier {br:.3f} → {bc:.3f})")
    ax.legend(loc="upper left", fontsize=8)
    ax.set_aspect("equal")
    save(fig, "fig06_calibration.png")


# ----------------------------------------------------- fig 7: sensor ADC hist -
def fig_leafwet_hist():
    lw = M["leafwet_validation"]
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    ax.hist(lw["adc_dry_samples"], bins=30, color=C_COMM, alpha=0.7, label="dry surface")
    ax.hist(lw["adc_wet_samples"], bins=30, color=C_FREE, alpha=0.7, label="wet surface")
    ax.axvline(
        lw["threshold_adc"],
        color="#333",
        ls="--",
        lw=1.3,
        label=f"threshold {lw['threshold_adc']:.0f}",
    )
    ax.set_xlabel("Leaf-wetness sensor ADC reading (12-bit)")
    ax.set_ylabel("count")
    ax.set_title(f"DIY leaf-wetness sensor: wet vs dry (acc {lw['accuracy'] * 100:.1f}%)")
    ax.legend(fontsize=8)
    save(fig, "fig07_leafwet_hist.png")


# ---------------------------------------------------- fig 8: confusion matrix -
def fig_confusion():
    c = M["leafwet_validation"]["confusion"]
    mat = np.array([[c["tn"], c["fp"]], [c["fn"], c["tp"]]])
    fig, ax = plt.subplots(figsize=(4.2, 4.0))
    im = ax.imshow(mat, cmap="Greens")
    ax.set_xticks([0, 1], ["pred dry", "pred wet"])
    ax.set_yticks([0, 1], ["true dry", "true wet"])
    for i in range(2):
        for j in range(2):
            ax.text(
                j,
                i,
                str(mat[i, j]),
                ha="center",
                va="center",
                color="white" if mat[i, j] > mat.max() / 2 else "black",
                fontsize=13,
            )
    ax.set_title("Leaf-wetness sensor confusion matrix")
    fig.colorbar(im, fraction=0.046, pad=0.04)
    save(fig, "fig08_leafwet_confusion.png")


# --------------------------------------------------------- fig 9: drift -------
def fig_drift():
    d = M["leafwet_validation"]["drift"]
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    ax.plot(
        d["weeks"],
        [a * 100 for a in d["accuracy_no_recal"]],
        "o-",
        color=C_FREE,
        label="no recalibration",
    )
    ax.plot(
        d["weeks"],
        [a * 100 for a in d["accuracy_recal"]],
        "s-",
        color=C_NODE,
        label="periodic recalibration",
    )
    ax.axhline(90, ls="--", color="#bbb", lw=1, label="90% target")
    ax.set_xlabel("weeks of field exposure")
    ax.set_ylabel("wet/dry accuracy (%)")
    ax.set_title("Electrode corrosion drift and its fix")
    ax.legend(fontsize=8)
    save(fig, "fig09_sensor_drift.png")


# ----------------------------------------------------- fig 10: spray reduction -
def fig_spray():
    sr = M["spray_reduction"]
    regions = ["konkan_humid", "gujarat_drier"]
    rlabels = ["Konkan\n(humid)", "Gujarat\n(drier)", "Overall"]
    cal = [sr["per_region"][r]["calendar_sprays_mean"] for r in regions] + [
        sr["overall"]["calendar_sprays_mean"]
    ]
    ew = [sr["per_region"][r]["early_warning_sprays_mean"] for r in regions] + [
        sr["overall"]["early_warning_sprays_mean"]
    ]
    cov = [sr["per_region"][r]["early_warning_coverage_highrisk"] for r in regions] + [
        sr["overall"]["early_warning_coverage_highrisk"]
    ]
    x = np.arange(len(rlabels))
    w = 0.36
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    ax.bar(x - w / 2, cal, w, color=C_CAL, label="calendar (fixed 8-day)")
    bars = ax.bar(x + w / 2, ew, w, color=C_NODE, label="node early-warning")
    for i, b in enumerate(bars):
        ax.text(
            b.get_x() + b.get_width() / 2,
            b.get_height() + 0.2,
            f"cover\n{cov[i] * 100:.0f}%",
            ha="center",
            fontsize=7.5,
            color=C_ACCENT,
        )
    ax.set_xticks(x, rlabels)
    ax.set_ylabel("fungicide sprays per season")
    ax.set_title("Fewer sprays, high-risk windows still covered")
    ax.legend(fontsize=8, loc="upper right")
    save(fig, "fig10_spray_reduction.png")


# ------------------------------------------------- fig 11: example season trace -
def fig_season_trace():
    from aamrakshak.eval.calibration import run_calibration
    from aamrakshak.riskengine.ppi import spray_schedule_calendar, spray_schedule_early_warning
    from aamrakshak.sim.outbreaks import add_outbreak_labels
    from aamrakshak.sim.weather import generate_panel

    seed = M["meta"]["seed"]
    panel = add_outbreak_labels(
        generate_panel(seed, n_seasons=M["meta"]["n_seasons"], n_blocks=M["meta"]["n_blocks"]), seed
    )
    _, cal_probs = run_calibration(panel, seed)
    panel = panel.reset_index(drop=True)
    panel["risk_pct"] = 100 * cal_probs
    # one humid Konkan block, last season (the held-out one)
    last = panel["season"].max()
    g = panel[
        (panel.region == "konkan_humid") & (panel.season == last) & (panel.block == 0)
    ].sort_values("day")
    risk = g["risk_pct"].to_numpy()
    days = g["day"].to_numpy()
    prob = g["outbreak_prob"].to_numpy()

    cal = [e.day for e in spray_schedule_calendar(len(g), 8)]
    ew = [
        e.day
        for e in spray_schedule_early_warning(risk, threshold=25, sustain_days=1, lockout_days=10)
    ]

    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    ax.plot(days, risk, color=C_NODE, lw=1.4, label="node risk %")
    ax.fill_between(
        days,
        0,
        100,
        where=(prob >= 0.5),
        color="#fdae61",
        alpha=0.25,
        label="true high-infection days",
    )
    ax.axhline(25, ls="--", color="#888", lw=1, label="spray threshold (25%)")
    for d in cal:
        ax.scatter(d, 92, marker="v", color=C_CAL, s=30, zorder=5)
    for d in ew:
        ax.scatter(d, 86, marker="v", color=C_ACCENT, s=34, zorder=5)
    ax.scatter([], [], marker="v", color=C_CAL, label=f"calendar sprays (n={len(cal)})")
    ax.scatter([], [], marker="v", color=C_ACCENT, label=f"early-warning sprays (n={len(ew)})")
    ax.set_xlabel("day of risk season")
    ax.set_ylabel("infection risk (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Illustrative season: node times sprays to risk (one Konkan block)")
    ax.legend(fontsize=7.5, loc="upper left", ncol=2)
    save(fig, "fig11_season_trace.png")


def main():
    print("Rendering figures ->", FIGS)
    fig_architecture()
    fig_hardware()
    fig_roc()
    fig_auc_bars()
    fig_ablation()
    fig_calibration()
    fig_leafwet_hist()
    fig_confusion()
    fig_drift()
    fig_spray()
    fig_season_trace()
    print("done.")


if __name__ == "__main__":
    main()
