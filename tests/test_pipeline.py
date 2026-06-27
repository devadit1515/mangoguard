"""End-to-end: the evaluation pipeline runs and all success conditions pass.

This is the regression guard for the report's headline numbers. If a change
breaks a success condition, this test fails loudly.
"""

from __future__ import annotations

import numpy as np

from aamrakshak.eval.ablation import run_ablation
from aamrakshak.eval.calibration import run_calibration
from aamrakshak.eval.leafwet_validation import run_leafwet_validation
from aamrakshak.eval.spray_reduction import run_spray_reduction
from aamrakshak.eval.tier_study import run_tier_study
from aamrakshak.sim.outbreaks import add_outbreak_labels
from aamrakshak.sim.weather import generate_panel

SEED = 20260627


def _panel():
    return add_outbreak_labels(generate_panel(SEED, n_seasons=3, n_blocks=4), SEED)


def test_tier_ordering_and_thresholds():
    panel = _panel()
    ts = run_tier_study(panel, SEED, n_seeds=4)
    t = ts["tiers"]
    # node beats free clearly (S1) and nearly matches commercial (S2).
    assert t["node"]["auc_mean"] >= 0.75
    assert t["node"]["auc_mean"] - t["free"]["auc_mean"] >= 0.10
    assert t["commercial"]["auc_mean"] - t["node"]["auc_mean"] <= 0.05
    # commercial >= node >= free >= calendar ordering holds.
    assert t["commercial"]["auc_mean"] >= t["node"]["auc_mean"] >= t["free"]["auc_mean"]


def test_calibration_improves_brier():
    panel = _panel()
    m, probs = run_calibration(panel, SEED)
    assert m["brier_calibrated_test"] < m["brier_raw_test"]
    assert len(probs) == len(panel)
    assert np.all((probs >= 0) & (probs <= 1))


def test_spray_reduction_S4():
    panel = _panel()
    _, probs = run_calibration(panel, SEED)
    sr = run_spray_reduction(panel, probs, chosen_threshold_pct=25.0)
    assert sr["overall"]["spray_reduction_pct"] >= 30.0
    assert sr["overall"]["early_warning_coverage_highrisk"] >= 0.90


def test_ablation_leaf_wetness_is_load_bearing():
    panel = _panel()
    ab = run_ablation(panel, SEED)
    assert ab["most_important"] == "leaf_wetness"
    drops = ab["auc_drop_when_removed"]
    # Leaf wetness drop dwarfs every other feature's.
    assert drops["leaf_wetness"] > 5 * max(abs(drops[k]) for k in drops if k != "leaf_wetness")


def test_sensor_validation_S3():
    lw = run_leafwet_validation(SEED)
    assert lw["accuracy"] >= 0.90
    c = lw["confusion"]
    assert c["tp"] + c["tn"] + c["fp"] + c["fn"] == lw["n_samples"]
