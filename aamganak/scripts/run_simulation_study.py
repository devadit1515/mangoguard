"""Score every estimator on the same simulated trees and write artifacts/sim_metrics.json.

One script produces every number the report cites, from one seed, so the report and the
data cannot drift apart. Reproduce with:  python scripts/run_simulation_study.py

The design:
  * trees are drawn across a range of canopy densities and fruit loads
  * every tree is scanned at each viewpoint count, so the viewpoint curve is within-tree
  * the calibration trees fit the fixed multiplier, exactly as the field fits it, and a
    separate multiplier is fitted per viewpoint count because that is what fairness needs
  * the test trees score all estimators on identical detections
so the only thing that differs between estimators is the estimator.

Viewpoint count is the primary axis. Occlusion falls away quickly as a walker adds
angles, so the question that decides whether this is usable on a real orchard is how
few viewpoints an estimator needs to match what naive counting achieves with many.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aamganak import canopy as C  # noqa: E402
from aamganak import estimators as E  # noqa: E402
from aamganak import visibility as V  # noqa: E402

SEED = 20260903
N_CAL, N_TEST = 20, 60
VIEW_COUNTS = [1, 2, 3, 4, 6, 12]
REFERENCE_VIEWS = 12  # what a patient operator would do
RECONSTRUCT_SAMPLES = 2500  # Monte Carlo points per tree for the carved-volume estimate
OUT = ROOT / "artifacts" / "sim_metrics.json"

# Leaf area density, calibrated to the leaf area index a bearing mango actually carries:
# 0.8 to 2.0 over a 3.6 m canopy is an LAI of 2.9 to 7.2 (see FIX_LOG entry 7).
LAD_RANGE = (0.8, 2.0)
FRUIT_RANGE = (120, 600)


def random_tree(rng: np.random.Generator) -> C.TreeParams:
    return C.TreeParams(
        radius=float(rng.uniform(1.8, 2.8)),
        half_height=float(rng.uniform(1.4, 2.2)),
        leaf_area_density=float(rng.uniform(*LAD_RANGE)),
        n_fruit=int(rng.integers(*FRUIT_RANGE)),
        shell_alpha=3.0,
        shell_beta=2.0,
    )


def make_population(n: int, rng: np.random.Generator):
    """Each tree scanned at every viewpoint count, so the curve is within-tree."""
    trees = []
    for _ in range(n):
        params = random_tree(rng)
        scans = {
            m: V.scan_tree(params, m, rng, reconstruct_samples=RECONSTRUCT_SAMPLES)
            for m in VIEW_COUNTS
        }
        trees.append(scans)
    return trees


def ape(estimate: float, truth: float) -> float:
    return abs(estimate - truth) / truth * 100.0


def main():
    rng = np.random.default_rng(SEED)
    cal = make_population(N_CAL, rng)
    test = make_population(N_TEST, rng)

    # The field fits its multiplier per imaging protocol, so it gets one per view count.
    k_by_views = {m: E.fit_multiplier([t[m] for t in cal]) for m in VIEW_COUNTS}

    def methods_for(m):
        return {
            "naive_visible_count": E.naive,
            "fixed_multiplier": lambda o, k=k_by_views[m]: E.fixed_multiplier(o, k),
            "capture_recapture": E.capture_recapture,
            "chao": E.chao,
            "horvitz_thompson": E.horvitz_thompson,
            "geometry_informed": E.geometry_informed,
            "reconstruction_informed": E.reconstruction_informed,
        }

    names = list(methods_for(VIEW_COUNTS[0]))
    per_view = {}
    rows = []
    for m in VIEW_COUNTS:
        methods = methods_for(m)
        apes = {n: [] for n in names}
        biases = {n: [] for n in names}
        for scans in test:
            observed, truth = scans[m]
            row = {
                "n_views": m,
                "n_fruit": truth["n_fruit"],
                "n_seen": truth["n_seen"],
                "visible_fraction": round(truth["visible_fraction"], 4),
                "never_visible_fraction": round(truth["never_visible_fraction"], 4),
                "leaf_area_density": round(observed["params"].leaf_area_density, 3),
            }
            for name, fn in methods.items():
                try:
                    est = float(fn(observed))
                except E.Unidentifiable:
                    row[name] = None  # not estimable from one viewpoint; see FIX_LOG 6
                    continue
                row[name] = round(est, 2)
                apes[name].append(ape(est, truth["n_fruit"]))
                biases[name].append((est - truth["n_fruit"]) / truth["n_fruit"] * 100.0)
            rows.append(row)
        per_view[m] = {
            name: (
                {
                    "mape": round(float(np.mean(apes[name])), 2),
                    "median_ape": round(float(np.median(apes[name])), 2),
                    "mean_bias_pct": round(float(np.mean(biases[name])), 2),
                }
                if apes[name]
                else {"mape": None, "median_ape": None, "mean_bias_pct": None}
            )
            for name in names
        }

    def vis_stats(m):
        sel = [r for r in rows if r["n_views"] == m]
        return {
            "mean_visible_fraction": round(float(np.mean([r["visible_fraction"] for r in sel])), 4),
            "mean_never_visible_fraction": round(
                float(np.mean([r["never_visible_fraction"] for r in sel])), 4
            ),
        }

    out = {
        "meta": {
            "seed": SEED,
            "n_calibration_trees": N_CAL,
            "n_test_trees": N_TEST,
            "view_counts": VIEW_COUNTS,
            "leaf_area_density_range": list(LAD_RANGE),
            "fruit_range": list(FRUIT_RANGE),
            "fitted_multiplier_by_views": {str(k): round(v, 4) for k, v in k_by_views.items()},
        },
        "visibility_by_views": {str(m): vis_stats(m) for m in VIEW_COUNTS},
        "accuracy_by_views": {str(m): per_view[m] for m in VIEW_COUNTS},
    }

    # The headline comparison: how few viewpoints does an estimator need to match naive
    # counting at the reference protocol?
    ref = per_view[REFERENCE_VIEWS]["naive_visible_count"]["mape"]
    matches = {}
    for name in names:
        hit = [
            m
            for m in VIEW_COUNTS
            if per_view[m][name]["mape"] is not None and per_view[m][name]["mape"] <= ref
        ]
        matches[name] = min(hit) if hit else None
    out["views_needed_to_match_naive_at_reference"] = {
        "reference_views": REFERENCE_VIEWS,
        "reference_mape": ref,
        "views_needed": matches,
    }

    # Where each estimator wins: accuracy split by canopy density as well as viewpoints.
    bands = {
        "open": lambda r: r["leaf_area_density"] < 1.2,
        "mid": lambda r: 1.2 <= r["leaf_area_density"] < 1.6,
        "dense": lambda r: r["leaf_area_density"] >= 1.6,
    }
    by_band = {}
    for band, pred in bands.items():
        by_band[band] = {}
        for m in VIEW_COUNTS:
            sel = [r for r in rows if r["n_views"] == m and pred(r)]
            entry = {}
            for name in names:
                vals = [ape(r[name], r["n_fruit"]) for r in sel if r.get(name) is not None]
                entry[name] = round(float(np.mean(vals)), 2) if vals else None
            entry["mean_visible_fraction"] = round(
                float(np.mean([r["visible_fraction"] for r in sel])), 4
            )
            by_band[band][str(m)] = entry
    out["accuracy_by_density_and_views"] = by_band

    # Interval coverage, at every protocol an operator might use. The first attempt
    # resampled the detected fruit and covered barely half of what it claimed; this is
    # the parametric bootstrap that replaced it (FIX_LOG entry 6).
    coverage = {}
    for m in [v for v in VIEW_COUNTS if v >= 2]:
        covered, widths = [], []
        for i, scans in enumerate(test):
            observed, truth = scans[m]
            try:
                lo, hi = E.parametric_interval(observed, n_boot=80, seed=SEED + i)
            except E.Unidentifiable:
                continue
            covered.append(lo <= truth["n_fruit"] <= hi)
            widths.append((hi - lo) / truth["n_fruit"] * 100.0)
        coverage[str(m)] = {
            "nominal": 0.90,
            "achieved": round(float(np.mean(covered)), 3) if covered else None,
            "mean_width_pct_of_truth": round(float(np.mean(widths)), 2) if widths else None,
            "n_trees": len(covered),
        }
    out["interval_coverage"] = coverage

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({**out, "per_tree": rows}, indent=2))

    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"{'views':>6}{'visible':>9}{'never':>8}" + "".join(f"{n[:11]:>12}" for n in names))
    for m in VIEW_COUNTS:
        v = out["visibility_by_views"][str(m)]
        line = f"{m:>6}{v['mean_visible_fraction']:>9.3f}{v['mean_never_visible_fraction']:>8.3f}"
        line += "".join(
            f"{per_view[m][n]['mape']:>12.2f}"
            if per_view[m][n]["mape"] is not None
            else f"{'n/a':>12}"
            for n in names
        )
        print(line)
    print()
    print(f"naive MAPE at {REFERENCE_VIEWS} views = {ref:.2f}%; views needed to match: {matches}")
    ic = out["interval_coverage_at_2_views"]
    print(
        f"90% interval coverage at 2 views: {ic['achieved']:.2f} (width {ic['mean_width_pct_of_truth']:.1f}%)"
    )


if __name__ == "__main__":
    main()
