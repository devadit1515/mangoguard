"""Sensor-tier discrimination study (success conditions S1, S2, S5).

Score every panel row under each sensor tier, compare against the independent
outbreak labels, and report ROC-AUC and Brier averaged over many sensor-noise
seeds (the ground truth is fixed; only the noise changes). Also breaks AUC down
by region for the generalisation check (S5).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from aamrakshak.eval.metrics import brier_score, roc_auc, roc_curve
from aamrakshak.sim.sensors import TIER_LABELS, tier_risk_scores


def run_tier_study(
    panel: pd.DataFrame,
    base_seed: int,
    n_seeds: int = 12,
    tiers: list[str] | None = None,
) -> dict:
    """Multi-seed AUC/Brier per tier, plus per-region AUC and ROC curves."""
    tiers = tiers or list(TIER_LABELS)
    y = panel["outbreak"].to_numpy()
    regions = sorted(panel["region"].unique())

    out: dict = {"tiers": {}, "roc_curves": {}}
    for tier in tiers:
        aucs, briers = [], []
        region_aucs = {r: [] for r in regions}
        for s in range(n_seeds):
            scores = tier_risk_scores(panel, tier, seed=base_seed + 100 + s)
            aucs.append(roc_auc(y, scores))
            briers.append(brier_score(y, scores))
            for r in regions:
                m = (panel["region"] == r).to_numpy()
                region_aucs[r].append(roc_auc(y[m], scores[m]))
        out["tiers"][tier] = {
            "label": TIER_LABELS[tier],
            "auc_mean": float(np.mean(aucs)),
            "auc_sd": float(np.std(aucs)),
            "brier_mean": float(np.mean(briers)),
            "brier_sd": float(np.std(briers)),
            "n_seeds": n_seeds,
            "auc_by_region": {
                r: {"mean": float(np.mean(region_aucs[r])), "sd": float(np.std(region_aucs[r]))}
                for r in regions
            },
        }
        # One representative ROC curve (fixed seed) for the figure.
        scores0 = tier_risk_scores(panel, tier, seed=base_seed + 100)
        fpr, tpr = roc_curve(y, scores0)
        out["roc_curves"][tier] = {
            "fpr": [round(float(x), 4) for x in fpr],
            "tpr": [round(float(x), 4) for x in tpr],
            "auc": float(roc_auc(y, scores0)),
            "label": TIER_LABELS[tier],
        }
    return out
