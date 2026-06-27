"""Probability calibration for the node tier (Platt scaling, train/test split).

ROC-AUC measures ranking; it says nothing about whether a "40% risk" day really
is a 40% day. The raw Akem score is uncalibrated against this region's base
rate, so before the score drives a spray threshold it is calibrated with Platt
scaling: fit a logistic of outbreak ~ logit(score) on the training seasons and
apply it to the held-out test season. Reported: test AUC (unchanged by a
monotone calibration), Brier before vs after, and reliability curves.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from aamrakshak.eval.metrics import brier_score, reliability_curve, roc_auc
from aamrakshak.sim.sensors import tier_risk_scores

_EPS = 1e-6


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, _EPS, 1.0 - _EPS)
    return np.log(p / (1.0 - p))


def run_calibration(panel: pd.DataFrame, base_seed: int) -> tuple[dict, np.ndarray]:
    """Calibrate node-tier risk; return metrics and calibrated probs (all rows).

    The last season is the held-out test set; earlier seasons train the Platt
    calibrator. The returned array is calibrated probability for every panel row
    (train rows via the fitted calibrator too), for downstream spray analysis.
    """
    raw = tier_risk_scores(panel, "node", seed=base_seed + 100)
    y = panel["outbreak"].to_numpy()
    seasons = np.sort(panel["season"].unique())
    test_season = seasons[-1]
    is_test = (panel["season"] == test_season).to_numpy()

    x_train = _logit(raw[~is_test]).reshape(-1, 1)
    clf = LogisticRegression()
    clf.fit(x_train, y[~is_test])

    cal_all = clf.predict_proba(_logit(raw).reshape(-1, 1))[:, 1]

    y_test = y[is_test]
    raw_test = raw[is_test]
    cal_test = cal_all[is_test]

    pr_raw, ob_raw, cnt_raw = reliability_curve(y_test, raw_test, n_bins=10)
    pr_cal, ob_cal, cnt_cal = reliability_curve(y_test, cal_test, n_bins=10)

    def _clean(a):
        return [None if np.isnan(v) else round(float(v), 4) for v in a]

    metrics = {
        "test_season": int(test_season),
        "n_train": int(np.sum(~is_test)),
        "n_test": int(np.sum(is_test)),
        "platt_coef": round(float(clf.coef_[0][0]), 4),
        "platt_intercept": round(float(clf.intercept_[0]), 4),
        "auc_test": round(float(roc_auc(y_test, raw_test)), 4),
        "brier_raw_test": round(float(brier_score(y_test, raw_test)), 4),
        "brier_calibrated_test": round(float(brier_score(y_test, cal_test)), 4),
        "reliability": {
            "raw": {
                "pred": _clean(pr_raw),
                "obs": _clean(ob_raw),
                "count": [int(c) for c in cnt_raw],
            },
            "calibrated": {
                "pred": _clean(pr_cal),
                "obs": _clean(ob_cal),
                "count": [int(c) for c in cnt_cal],
            },
        },
    }
    return metrics, cal_all
