"""Run the full AamRakshak evaluation and write artifacts/eval_metrics.json.

Every headline number in the report comes from this one script. Ground truth is
generated once from a fixed seed; only sensor noise varies between tiers and
seeds. Run from the repo root:

    python scripts/run_evaluation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aamrakshak import __version__  # noqa: E402
from aamrakshak.eval.ablation import run_ablation  # noqa: E402
from aamrakshak.eval.calibration import run_calibration  # noqa: E402
from aamrakshak.eval.leafwet_validation import run_leafwet_validation  # noqa: E402
from aamrakshak.eval.spray_reduction import run_spray_reduction  # noqa: E402
from aamrakshak.eval.tier_study import run_tier_study  # noqa: E402
from aamrakshak.sim.outbreaks import OUTBREAK_COEFFS, add_outbreak_labels  # noqa: E402
from aamrakshak.sim.weather import SEASON_DAYS, generate_panel  # noqa: E402

SEED = 20260627
N_SEASONS = 3
N_BLOCKS = 4
N_NOISE_SEEDS = 12
CHOSEN_SPRAY_THRESHOLD_PCT = 25.0


def evaluate_success_conditions(m: dict) -> dict:
    """Pass/fail each pre-registered success condition from the results."""
    t = m["tier_study"]["tiers"]
    node_auc = t["node"]["auc_mean"]
    free_auc = t["free"]["auc_mean"]
    comm_auc = t["commercial"]["auc_mean"]
    node_regions = t["node"]["auc_by_region"]
    sr = m["spray_reduction"]["overall"]
    lw_acc = m["leafwet_validation"]["accuracy"]

    s5_region_min = min(v["mean"] for v in node_regions.values())
    s5_region_max = max(v["mean"] for v in node_regions.values())
    return {
        "S1_leaf_wetness_decisive": {
            "pass": bool(node_auc >= 0.75 and (node_auc - free_auc) >= 0.10),
            "node_auc": round(node_auc, 4),
            "free_auc": round(free_auc, 4),
            "gap": round(node_auc - free_auc, 4),
        },
        "S2_node_matches_station": {
            "pass": bool((comm_auc - node_auc) <= 0.05),
            "node_auc": round(node_auc, 4),
            "commercial_auc": round(comm_auc, 4),
            "gap": round(comm_auc - node_auc, 4),
        },
        "S3_sensor_trustworthy": {
            "pass": bool(lw_acc >= 0.90),
            "accuracy": lw_acc,
        },
        "S4_fewer_sprays_no_missed_windows": {
            "pass": bool(
                sr["spray_reduction_pct"] >= 30.0 and sr["early_warning_coverage_highrisk"] >= 0.90
            ),
            "spray_reduction_pct": sr["spray_reduction_pct"],
            "early_warning_coverage_highrisk": sr["early_warning_coverage_highrisk"],
            "calendar_coverage_highrisk": sr["calendar_coverage_highrisk"],
        },
        "S5_generalises_across_regions": {
            # Region-vs-region (not vs the pooled AUC, which inflates with two
            # base rates): each region clears 0.75 and the regions agree closely.
            "pass": bool(s5_region_min >= 0.75 and (s5_region_max - s5_region_min) <= 0.05),
            "node_auc_by_region": {k: round(v["mean"], 4) for k, v in node_regions.items()},
            "worst_region_auc": round(s5_region_min, 4),
            "region_spread": round(s5_region_max - s5_region_min, 4),
        },
    }


def main() -> None:
    panel = generate_panel(SEED, n_seasons=N_SEASONS, n_blocks=N_BLOCKS)
    panel = add_outbreak_labels(panel, SEED)

    metrics: dict = {
        "meta": {
            "package_version": __version__,
            "seed": SEED,
            "n_seasons": N_SEASONS,
            "n_blocks": N_BLOCKS,
            "season_days": SEASON_DAYS,
            "n_noise_seeds": N_NOISE_SEEDS,
            "regions": sorted(panel["region"].unique().tolist()),
            "outbreak_generator_coeffs": OUTBREAK_COEFFS,
            "note": "All weather and outbreak labels are SIMULATED from documented "
            "climate normals and an independent epidemiological generator. Leaf-"
            "wetness sensor validation uses an emulated-but-grounded bench model. "
            "See docs/DESIGN.md and the report's data-provenance appendix.",
        },
        "panel": {
            "n_rows": int(len(panel)),
            "n_outbreaks": int(panel["outbreak"].sum()),
            "outbreak_rate": round(float(panel["outbreak"].mean()), 4),
            "outbreak_rate_by_region": {
                r: round(float(panel.loc[panel["region"] == r, "outbreak"].mean()), 4)
                for r in sorted(panel["region"].unique())
            },
        },
    }

    metrics["tier_study"] = run_tier_study(panel, SEED, n_seeds=N_NOISE_SEEDS)
    cal_metrics, cal_probs = run_calibration(panel, SEED)
    metrics["calibration"] = cal_metrics
    metrics["spray_reduction"] = run_spray_reduction(
        panel, cal_probs, chosen_threshold_pct=CHOSEN_SPRAY_THRESHOLD_PCT
    )
    metrics["leafwet_validation"] = run_leafwet_validation(SEED)
    metrics["ablation"] = run_ablation(panel, SEED)
    metrics["success_conditions"] = evaluate_success_conditions(metrics)

    out = ROOT / "artifacts" / "eval_metrics.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    # Console summary.
    t = metrics["tier_study"]["tiers"]
    print(
        f"AamRakshak evaluation  (seed={SEED}, n={metrics['panel']['n_rows']} block-days, "
        f"outbreak rate={metrics['panel']['outbreak_rate']:.0%})"
    )
    print("-" * 66)
    for k in ("calendar", "free", "node", "commercial"):
        print(f"  {t[k]['label']:<48} AUC={t[k]['auc_mean']:.3f} +/- {t[k]['auc_sd']:.3f}")
    print("-" * 66)
    for name, sc in metrics["success_conditions"].items():
        print(f"  [{'PASS' if sc['pass'] else 'FAIL'}] {name}")
    print(f"\nWrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
