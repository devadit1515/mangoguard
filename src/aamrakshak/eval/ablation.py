"""Leave-one-feature-out ablation on the node tier.

Quantifies the project's central thesis: leaf wetness is the load-bearing
signal. Each input is neutralised in turn (replaced by its mean, so it carries
no information) and the AUC drop is measured. The biggest drop names the most
important feature.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from aamrakshak.eval.metrics import roc_auc
from aamrakshak.sim.sensors import _vec_anthracnose_risk


def run_ablation(panel: pd.DataFrame, base_seed: int) -> dict:
    """Full node AUC vs AUC with each feature neutralised."""
    rng = np.random.default_rng(base_seed + 100)
    n = len(panel)
    y = panel["outbreak"].to_numpy()

    t_max = panel["t_max"].to_numpy() + rng.normal(0.0, 0.4, n)
    t_min = panel["t_min"].to_numpy() + rng.normal(0.0, 0.4, n)
    rh = np.clip(panel["rh_morning"].to_numpy() + rng.normal(0.0, 2.5, n), 25.0, 100.0)
    lw = np.clip(panel["leaf_wetness_true"].to_numpy() + rng.normal(0.0, 1.2, n), 0.0, 18.0)
    sun = panel["district_sunshine"].to_numpy()
    wind = panel["district_wind"].to_numpy()

    full = roc_auc(y, _vec_anthracnose_risk(t_max, t_min, rh, lw, sun, wind))

    def auc_without(feature: str) -> float:
        a = dict(t_max=t_max, t_min=t_min, rh=rh, lw=lw, sun=sun, wind=wind)
        if feature == "leaf_wetness":
            a["lw"] = np.full(n, float(np.mean(lw)))
        elif feature == "humidity":
            a["rh"] = np.full(n, float(np.mean(rh)))
        elif feature == "temp_range":
            mean_range = float(np.mean(t_max - t_min))
            mid = 0.5 * (t_max + t_min)
            a["t_max"] = mid + mean_range / 2
            a["t_min"] = mid - mean_range / 2
        elif feature == "sunshine":
            a["sun"] = np.full(n, float(np.mean(sun)))
        elif feature == "wind":
            a["wind"] = np.full(n, float(np.mean(wind)))
        risk = _vec_anthracnose_risk(a["t_max"], a["t_min"], a["rh"], a["lw"], a["sun"], a["wind"])
        return roc_auc(y, risk)

    features = ["leaf_wetness", "humidity", "temp_range", "sunshine", "wind"]
    drops = {f: round(float(full - auc_without(f)), 4) for f in features}
    return {
        "auc_full": round(float(full), 4),
        "auc_drop_when_removed": drops,
        "most_important": max(drops, key=drops.get),
    }
