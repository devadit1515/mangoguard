"""Render every figure in the report from the data and eval_metrics.json.

Reproduce with:  python scripts/make_figures.py   (after run_evaluation.py)
Figures are written to artifacts/figs/ at 300 dpi.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from aamparakh import data as D  # noqa: E402
from aamparakh import models as M  # noqa: E402
from aamparakh import sensors as S  # noqa: E402

FIGS = ROOT / "artifacts" / "figs"
FIGS.mkdir(parents=True, exist_ok=True)
MET = json.loads((ROOT / "artifacts" / "eval_metrics.json").read_text())
INK, ACC, WARN, GREY = "#1b3a2f", "#2e8b57", "#c25b2e", "#8a9691"
plt.rcParams.update(
    {
        "font.size": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 300,
        "savefig.bbox": "tight",
    }
)


def save(fig, name):
    fig.savefig(FIGS / name, dpi=300)
    plt.close(fig)
    print("wrote", name)


def main():
    df = D.load_dataset()
    cal, tun, test = D.cal_tune_test(df)
    wl = D.wavelengths(df)
    yc, yt, ye = cal[D.TARGET].to_numpy(), tun[D.TARGET].to_numpy(), test[D.TARGET].to_numpy()

    # refit the two headline models for scatter plots
    Xc, _ = D.spectra(cal, D.DMC_WINDOW)
    Xt, _ = D.spectra(tun, D.DMC_WINDOW)
    Xe, _ = D.spectra(test, D.DMC_WINDOW)
    full = M.FullSpectrumModel().fit(Xc, yc, Xt, yt)
    pe_full = full.predict(Xe)

    def dev_bands(g):
        X, _ = D.spectra(g)
        return S.simulate_bands(X, wl, S.DEVICE_BANDS)

    dev = M.BandModel("pls").fit(dev_bands(cal), yc, dev_bands(tun), yt)
    pe_dev = dev.predict(dev_bands(test))

    # 1. dry-matter distribution
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.hist(df[D.TARGET], bins=40, color=ACC, alpha=0.85)
    ax.axvline(15, color=WARN, ls="--", lw=1.5, label="harvest line (15% DM)")
    ax.set_xlabel("dry matter content (% fresh weight)")
    ax.set_ylabel("fruit")
    ax.set_title(f"Dry matter across {len(df):,} fruit, 10 cultivars, 4 seasons")
    ax.legend(frameon=False)
    save(fig, "fig01_dm_distribution.png")

    # 2 & 3. predicted vs measured, full spectrum and device
    for pe, tag, r2, rmsep, fname in [
        (
            pe_full,
            "Full research spectrum (103 wavelengths)",
            MET["full_spectrum"]["r2"],
            MET["full_spectrum"]["rmsep"],
            "fig02_full_spectrum_scatter.png",
        ),
        (
            pe_dev,
            "AamParakh device (8 NIR LEDs)",
            MET["device"]["r2"],
            MET["device"]["rmsep"],
            "fig03_device_scatter.png",
        ),
    ]:
        fig, ax = plt.subplots(figsize=(4.6, 4.6))
        ax.scatter(ye, pe, s=6, alpha=0.25, color=ACC, edgecolors="none")
        lo, hi = 8, 26
        ax.plot([lo, hi], [lo, hi], color=INK, lw=1)
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.set_xlabel("measured DM (%)")
        ax.set_ylabel("predicted DM (%)")
        ax.set_title(f"{tag}\nR2 = {r2:.2f}, RMSEP = {rmsep:.2f}% DM")
        save(fig, fname)

    # 4. band-count curve
    curve = MET["band_count_curve"]
    ks = [c["k"] for c in curve]
    r2s = [c["test_r2"] for c in curve]
    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.plot(ks, r2s, "-o", color=ACC, lw=2)
    ax.axhline(MET["full_spectrum"]["r2"], color=INK, ls="--", lw=1.2, label="full spectrum")
    ax.axhline(0.95 * MET["full_spectrum"]["r2"], color=GREY, ls=":", lw=1.2, label="95% of full")
    ax.set_xlabel("number of NIR LEDs (added best-first)")
    ax.set_ylabel("R2 on 2018 test season")
    ax.set_title("How few LEDs are enough")
    ax.set_ylim(-0.6, 1)
    ax.legend(frameon=False, loc="lower right")
    save(fig, "fig04_band_count_curve.png")

    # 5. device vs off-the-shelf vs lab, R2 bars
    labels = [
        "Full lab\nspectrum",
        "AamParakh\n8 LEDs",
        "AS7265x\n(off-shelf)",
        "AS7263\n(off-shelf)",
    ]
    vals = [
        MET["full_spectrum"]["r2"],
        MET["device"]["r2"],
        MET["off_the_shelf"]["AS7265x"]["r2"],
        MET["off_the_shelf"]["AS7263"]["r2"],
    ]
    cols = [INK, ACC, WARN, WARN]
    fig, ax = plt.subplots(figsize=(6, 3.8))
    bars = ax.bar(labels, vals, color=cols)
    ax.axhline(0, color="k", lw=0.8)
    for b, v in zip(bars, vals, strict=True):
        ax.text(
            b.get_x() + b.get_width() / 2,
            v + (0.02 if v >= 0 else -0.06),
            f"{v:.2f}",
            ha="center",
            fontsize=10,
        )
    ax.set_ylabel("R2 (2018 test season)")
    ax.set_title("The right 8 bands match the lab; off-the-shelf chips do not")
    save(fig, "fig05_tier_comparison.png")

    # 6. mean spectrum with the device LEDs marked
    Xall, _ = D.spectra(df)
    mean_spec = Xall.mean(axis=0)
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.plot(wl, mean_spec, color=GREY, lw=1.5)
    order = MET["led_selection_order_nm"]
    for rank, c in enumerate(order):
        col = ACC if rank < MET["min_leds_for_95pct_full_r2"] else WARN
        ax.axvline(c, color=col, lw=1.6, alpha=0.9)
        ax.text(
            c, ax.get_ylim()[1], str(c), rotation=90, va="top", ha="right", fontsize=7, color=col
        )
    ax.set_xlim(650, 1050)
    ax.set_xlabel("wavelength (nm)")
    ax.set_ylabel("mean reflectance (a.u.)")
    ax.set_title("Where the dry-matter signal lives (green = the 5 that matter most)")
    save(fig, "fig06_selected_bands.png")

    # 7. cross-cultivar robustness
    loco = MET["cross_cultivar_loco"]
    names = list(loco)
    r2v = [loco[n]["r2"] for n in names]
    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.bar(names, r2v, color=ACC)
    ax.axhline(MET["device"]["r2"], color=INK, ls="--", lw=1.2, label="all-cultivar device")
    ax.set_ylabel("R2 on the held-out cultivar")
    ax.set_ylim(0, 1)
    ax.set_title("Trained without each cultivar, tested on it")
    ax.legend(frameon=False)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    save(fig, "fig07_cross_cultivar.png")

    # 8. harvest-readiness confusion (device)
    h = MET["device"]["harvest"]
    cm = np.array([[h["tn"], h["fp"]], [h["fn"], h["tp"]]])
    fig, ax = plt.subplots(figsize=(4.2, 4))
    ax.imshow(cm, cmap="Greens")
    for (i, j), v in np.ndenumerate(cm):
        ax.text(
            j,
            i,
            str(v),
            ha="center",
            va="center",
            color="white" if v > cm.max() / 2 else INK,
            fontsize=13,
        )
    ax.set_xticks([0, 1], ["not ready", "ready"])
    ax.set_yticks([0, 1], ["not ready", "ready"])
    ax.set_xlabel("device call")
    ax.set_ylabel("true (from DM)")
    ax.set_title(f"Harvest-readiness calls\naccuracy {h['accuracy'] * 100:.0f}%")
    save(fig, "fig08_harvest_confusion.png")

    # 9. calibration / farm transfer before-after
    farm = MET["farm_validation"]
    stages = ["device as shipped", "after 20 local fruit"]
    rmseps = [farm["before_recal"]["rmsep"], farm["after_local_recal"]["rmsep"]]
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    ax.bar(stages, rmseps, color=[WARN, ACC])
    for i, v in enumerate(rmseps):
        ax.text(i, v + 0.05, f"{v:.2f}", ha="center")
    ax.set_ylabel("RMSEP on local fruit (% DM)")
    ax.set_title("A short local calibration fixes the new-cultivar bias")
    save(fig, "fig09_local_calibration.png")

    print("all figures written to", FIGS.relative_to(ROOT))


if __name__ == "__main__":
    main()
