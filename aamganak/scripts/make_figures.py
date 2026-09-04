"""Redraw every figure from artifacts/sim_metrics.json.

Reproduce with:  python scripts/make_figures.py   (after run_simulation_study.py)
Figures land in artifacts/figs/ at 300 dpi. Nothing here recomputes a result; every
number plotted is read from the metrics file, so a figure cannot disagree with the text.
The one exception is the canopy cross-section, which re-simulates a single tree from a
fixed seed purely to draw it.
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
from matplotlib.patches import Patch  # noqa: E402

from aamganak import canopy as C  # noqa: E402
from aamganak import reconstruct as R  # noqa: E402
from aamganak import visibility as V  # noqa: E402

FIGS = ROOT / "artifacts" / "figs"
FIGS.mkdir(parents=True, exist_ok=True)
MET = json.loads((ROOT / "artifacts" / "sim_metrics.json").read_text())

INK, GREEN, ORANGE, GREY, BLUE = "#1b2a33", "#2e7d5b", "#c2703e", "#93a1a8", "#3a6ea5"
plt.rcParams.update(
    {
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linewidth": 0.6,
        "figure.dpi": 300,
        "savefig.bbox": "tight",
    }
)

# Published field figures, for reference lines. Wang, Walsh and Koirala (2019).
PUBLISHED_DUAL_VIEW = 0.402
PUBLISHED_VIDEO_TRACK = 0.623

LABELS = {
    "naive_visible_count": "count what is seen",
    "fixed_multiplier": "fitted multiplier",
    "capture_recapture": "capture-recapture",
    "chao": "Chao",
    "horvitz_thompson": "Horvitz-Thompson",
    "geometry_informed": "canopy-depth model",
    "reconstruction_informed": "reconstruction",
}
STYLE = {
    "naive_visible_count": (GREY, "-", "o"),
    "fixed_multiplier": (ORANGE, "-", "s"),
    "capture_recapture": (BLUE, "--", "^"),
    "chao": (BLUE, ":", "v"),
    "horvitz_thompson": (INK, "--", "D"),
    "geometry_informed": (INK, ":", "P"),
    "reconstruction_informed": (GREEN, "-", "o"),
}
VIEWS = MET["meta"]["view_counts"]


def save(fig, name):
    fig.savefig(FIGS / name, dpi=300)
    plt.close(fig)
    print("wrote", name)


def fig_visibility():
    """How much of the crop a camera can see, and how that compares with the field."""
    vis = [MET["visibility_by_views"][str(v)]["mean_visible_fraction"] for v in VIEWS]
    never = [MET["visibility_by_views"][str(v)]["mean_never_visible_fraction"] for v in VIEWS]
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    ax.plot(VIEWS, vis, "-o", color=GREEN, lw=2, label="seen at least once")
    ax.plot(VIEWS, never, "-o", color=ORANGE, lw=2, label="never seen from anywhere")
    ax.axhline(PUBLISHED_DUAL_VIEW, color=GREY, ls="--", lw=1.2)
    ax.axhline(PUBLISHED_VIDEO_TRACK, color=GREY, ls=":", lw=1.2)
    ax.text(
        11.6, PUBLISHED_DUAL_VIEW + 0.015, "field, dual view", ha="right", fontsize=8, color=INK
    )
    ax.text(
        11.6,
        PUBLISHED_VIDEO_TRACK + 0.015,
        "field, video tracking",
        ha="right",
        fontsize=8,
        color=INK,
    )
    ax.set_xlabel("viewpoints around the tree")
    ax.set_ylabel("fraction of the fruit on the tree")
    ax.set_ylim(0, 1)
    ax.set_xticks(VIEWS)
    ax.set_title("What a camera sees, against harvest-validated field counts")
    ax.legend(frameon=False, loc="center right")
    save(fig, "fig1_visibility_vs_views.png")


def fig_accuracy():
    """The headline: error against effort, for every estimator."""
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    for name, (colour, ls, marker) in STYLE.items():
        xs, ys = [], []
        for v in VIEWS:
            val = MET["accuracy_by_views"][str(v)][name]["mape"]
            if val is not None:
                xs.append(v)
                ys.append(val)
        lw = 2.4 if name == "reconstruction_informed" else 1.3
        ax.plot(xs, ys, ls, marker=marker, color=colour, lw=lw, ms=4, label=LABELS[name])
    ref = MET["views_needed_to_match_naive_at_reference"]["reference_mape"]
    ax.axhline(ref, color=GREY, lw=1, ls="--")
    ax.text(1.05, ref + 0.6, f"counting what is seen, at 12 viewpoints ({ref:.1f}%)", fontsize=8)
    ax.set_yscale("log")
    ax.set_xticks(VIEWS)
    ax.set_yticks([1, 2, 5, 10, 20, 40])
    ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_xlabel("viewpoints around the tree")
    ax.set_ylabel("mean absolute error in fruit count (%)")
    ax.set_title("Error against effort")
    ax.legend(frameon=False, fontsize=8, ncol=2)
    save(fig, "fig2_accuracy_vs_views.png")


def fig_effort_saving():
    """How many viewpoints each method needs to match plain counting at twelve."""
    needed = MET["views_needed_to_match_naive_at_reference"]["views_needed"]
    order = [k for k in STYLE if needed.get(k)]
    vals = [needed[k] for k in order]
    fig, ax = plt.subplots(figsize=(6.0, 3.2))
    colours = [STYLE[k][0] for k in order]
    bars = ax.barh([LABELS[k] for k in order], vals, color=colours)
    for b, v in zip(bars, vals, strict=True):
        ax.text(v + 0.15, b.get_y() + b.get_height() / 2, str(v), va="center", fontsize=9)
    ax.set_xlabel("viewpoints needed to match plain counting at twelve viewpoints")
    ax.set_xlim(0, 13)
    ax.set_title("The same accuracy, for less walking")
    ax.grid(axis="y", visible=False)
    save(fig, "fig3_effort_saving.png")


def fig_density_bands():
    """Where each method wins, split by how dense the canopy is."""
    bands = ["open", "mid", "dense"]
    titles = {"open": "open canopy", "mid": "medium", "dense": "dense canopy"}
    shown = [
        "naive_visible_count",
        "fixed_multiplier",
        "capture_recapture",
        "reconstruction_informed",
    ]
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.2), sharey=True)
    for ax, band in zip(axes, bands, strict=True):
        for name in shown:
            xs, ys = [], []
            for v in VIEWS:
                val = MET["accuracy_by_density_and_views"][band][str(v)][name]
                if val is not None:
                    xs.append(v)
                    ys.append(val)
            colour, ls, marker = STYLE[name]
            lw = 2.2 if name == "reconstruction_informed" else 1.2
            ax.plot(xs, ys, ls, marker=marker, color=colour, lw=lw, ms=3.5, label=LABELS[name])
        vis = MET["accuracy_by_density_and_views"][band]["2"]["mean_visible_fraction"]
        ax.set_title(f"{titles[band]}\n{vis:.0%} seen at two viewpoints", fontsize=9)
        ax.set_yscale("log")
        ax.set_xticks(VIEWS)
        ax.set_xlabel("viewpoints")
    axes[0].set_ylabel("mean absolute error (%)")
    axes[0].set_yticks([1, 2, 5, 10, 20, 40])
    axes[0].get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    axes[-1].legend(frameon=False, fontsize=8)
    fig.suptitle("The denser the canopy, the more the correction is worth", y=1.04, fontsize=11)
    save(fig, "fig4_density_bands.png")


def fig_canopy_slice():
    """A vertical slice through one tree, showing what the cameras could reach.

    This is the idea in a picture. Shaded cells were seen from at least one camera
    position, so a fruit there had a chance of being counted, and the shade says from how
    many. The charcoal region was seen from none of them: a fruit there leaves no trace
    in any image and none in the detection histories either. Its volume is what the
    reconstruction measures and what the estimator fills.

    Blues rather than greens, because the colour that means "never seen" has to be
    unmistakable against every shade that means "seen", and the dark end of a green scale
    is not.
    """
    rng = np.random.default_rng(7)
    params = C.TreeParams(leaf_area_density=1.6, n_fruit=320, radius=2.3, half_height=1.8)
    grid = V.FoliageGrid(params, rng)
    fruit = C.sample_fruit(params, rng)

    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.2), sharey=True)
    seen_cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "seen", ["#dbe9f6", "#9ecae1", "#4a90c4", "#2166ac"]
    )
    images = []
    for ax, n_views in zip(axes, (2, 6), strict=True):
        cameras = V.camera_ring(n_views, centre_height=params.centre_height)
        nx, nz = 150, 130
        xs = np.linspace(-params.radius, params.radius, nx)
        zs = np.linspace(
            params.centre_height - params.half_height,
            params.centre_height + params.half_height,
            nz,
        )
        gx, gz = np.meshgrid(xs, zs)
        pts = np.column_stack([gx.ravel(), np.zeros(gx.size), gz.ravel()])
        inside = np.sum(((pts - params.centre) / params.axes) ** 2, axis=1) <= 1.0
        seen = np.full(pts.shape[0], np.nan)
        seen[inside] = R.clear_view_counts(pts[inside], cameras, grid)
        img = seen.reshape(nz, nx)
        extent = [xs[0], xs[-1], zs[0], zs[-1]]

        hidden = np.ma.masked_where(~(img == 0), np.ones_like(img))
        # Shown as the share of viewpoints rather than the count, so the two panels use
        # one scale. Plotting the raw count would give the left panel a darkest shade
        # meaning two and the right panel a darkest shade meaning six, against a single
        # colour bar, which would read as the same value.
        visible = np.ma.masked_where(~(img > 0), img / n_views)
        im = ax.imshow(
            visible,
            origin="lower",
            extent=extent,
            cmap=seen_cmap,
            vmin=0.0,
            vmax=1.0,
            aspect="equal",
        )
        images.append(im)
        ax.imshow(
            hidden,
            origin="lower",
            extent=extent,
            cmap=matplotlib.colors.ListedColormap(["#33383d"]),
            aspect="equal",
        )
        near = np.abs(fruit[:, 1]) < 0.25
        ax.scatter(
            fruit[near, 0],
            fruit[near, 2],
            s=9,
            color="#e8622a",
            edgecolors="white",
            linewidths=0.3,
            zorder=3,
        )
        hidden_pct = float(np.nanmean(img[~np.isnan(img)] == 0))
        ax.set_title(f"{n_views} viewpoints - {hidden_pct:.0%} of the canopy unseen", fontsize=10)
        ax.set_xlabel("metres from the trunk")
        ax.grid(visible=False)
    axes[0].set_ylabel("height (m)")

    cbar = fig.colorbar(images[-1], ax=axes, fraction=0.03, pad=0.02)
    cbar.set_label("share of viewpoints with a clear line of sight", fontsize=9)
    cbar.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
    cbar.set_ticklabels(["0", "¼", "½", "¾", "all"])
    handles = [
        Patch(facecolor="#33383d", label="never seen from any viewpoint"),
        plt.Line2D(
            [],
            [],
            marker="o",
            ls="",
            color="#e8622a",
            markersize=5,
            markeredgecolor="white",
            label="fruit near this slice",
        ),
    ]
    fig.legend(
        handles=handles,
        frameon=False,
        fontsize=9,
        ncol=2,
        loc="lower center",
        bbox_to_anchor=(0.45, -0.06),
    )
    fig.suptitle("A slice through the canopy: what the cameras could reach", y=1.02, fontsize=11)
    save(fig, "fig5_canopy_slice.png")


def fig_scatter():
    """Estimated against true count, at the protocol an operator would use."""
    rows = [r for r in MET["per_tree"] if r["n_views"] == 3]
    truth = np.array([r["n_fruit"] for r in rows], float)
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 4.2), sharex=True, sharey=True)
    for ax, name in zip(axes, ("fixed_multiplier", "reconstruction_informed"), strict=True):
        est = np.array([r[name] for r in rows], float)
        ax.scatter(truth, est, s=16, color=STYLE[name][0], alpha=0.75, edgecolors="none")
        lo, hi = 80, 640
        ax.plot([lo, hi], [lo, hi], color=INK, lw=1)
        mape = MET["accuracy_by_views"]["3"][name]["mape"]
        ax.set_title(f"{LABELS[name]}\nmean absolute error {mape:.2f}%", fontsize=10)
        ax.set_xlabel("fruit actually on the tree")
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
    axes[0].set_ylabel("estimated fruit")
    fig.suptitle("Three viewpoints per tree", y=1.0, fontsize=11)
    save(fig, "fig6_scatter_at_three_views.png")


def fig_intervals():
    """What the prediction intervals actually deliver against what they claim."""
    cov = MET["interval_coverage"]
    views = [int(k) for k in cov if cov[k]["achieved"] is not None]
    achieved = [cov[str(v)]["achieved"] for v in views]
    widths = [cov[str(v)]["mean_width_pct_of_truth"] for v in views]
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    ax.plot(views, achieved, "-o", color=GREEN, lw=2, label="coverage achieved")
    ax.axhline(0.90, color=ORANGE, ls="--", lw=1.4, label="coverage claimed")
    ax.set_ylim(0.5, 1.05)
    ax.set_xticks(views)
    ax.set_xlabel("viewpoints around the tree")
    ax.set_ylabel("share of trees inside the interval")
    ax2 = ax.twinx()
    ax2.plot(views, widths, "-s", color=GREY, lw=1.2, ms=4, label="interval width")
    ax2.set_ylabel("interval width (% of true count)")
    ax2.set_ylim(0, 30)
    ax2.grid(visible=False)
    lines = ax.get_lines()[:1] + [ax.get_lines()[1]] + ax2.get_lines()
    ax.legend(lines, [ln.get_label() for ln in lines], frameon=False, fontsize=8, loc="lower right")
    ax.set_title("The intervals cover more than they claim")
    save(fig, "fig7_interval_coverage.png")


def main():
    fig_visibility()
    fig_accuracy()
    fig_effort_saving()
    fig_density_bands()
    fig_canopy_slice()
    fig_scatter()
    fig_intervals()
    print("all figures written to", FIGS.relative_to(ROOT))


if __name__ == "__main__":
    main()
