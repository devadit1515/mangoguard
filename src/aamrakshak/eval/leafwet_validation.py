"""Bench validation of the DIY leaf-wetness sensor (success condition S3).

Generates a labelled bench dataset of wet and dry surface states, reads the
modelled interdigitated grid, calibrates a midpoint threshold, and reports
classification quality. Also quantifies corrosion drift: how accuracy decays
over weeks of DC excitation, and how a periodic recalibration recovers it (the
documented mitigation in the build guide and firmware).

Bench note: these are emulated sensor electronics with physically-grounded
response and noise, stated honestly. A student building the node reproduces the
same procedure with a spray bottle and a dry cloth against the real board.
"""

from __future__ import annotations

import numpy as np

from aamrakshak.eval.metrics import classification_report
from aamrakshak.riskengine.leafwetness import LeafWetnessSensor


def run_leafwet_validation(seed: int, n_samples: int = 600) -> dict:
    """Calibrate + score the DIY leaf-wetness sensor; quantify drift."""
    rng = np.random.default_rng(seed)
    sensor = LeafWetnessSensor()

    # Balanced bench trials: half wet, half dry.
    n_half = n_samples // 2
    wet_w = rng.uniform(0.70, 1.0, n_half)  # surface-water fraction when wet
    dry_w = rng.uniform(0.0, 0.20, n_half)  # residual film when dry
    adc_wet = np.array([sensor.read_adc(w, rng) for w in wet_w])
    adc_dry = np.array([sensor.read_adc(w, rng) for w in dry_w])

    adc = np.concatenate([adc_wet, adc_dry])
    y_true = np.concatenate([np.ones(n_half, int), np.zeros(n_half, int)])
    thr = sensor.calibration_threshold()
    y_pred = (adc < thr).astype(int)
    report = classification_report(y_true, y_pred)

    # Corrosion drift: wet readings creep upward; recalibrate periodically.
    drift_per_week = 130.0
    weeks = [0, 2, 4, 6, 8]
    acc_no_recal, acc_recal = [], []
    for wk in weeks:
        drifted = LeafWetnessSensor(drift_counts=drift_per_week * wk)
        a_wet = np.array([drifted.read_adc(w, rng) for w in wet_w])
        a_dry = np.array([drifted.read_adc(w, rng) for w in dry_w])
        a = np.concatenate([a_wet, a_dry])
        # Without recalibration: keep the week-0 threshold.
        p_no = (a < thr).astype(int)
        acc_no_recal.append(classification_report(y_true, p_no)["accuracy"])
        # With recalibration: threshold tracks the drifted anchors.
        p_re = (a < drifted.calibration_threshold()).astype(int)
        acc_recal.append(classification_report(y_true, p_re)["accuracy"])

    return {
        "n_samples": n_samples,
        "threshold_adc": round(float(thr), 1),
        "accuracy": round(float(report["accuracy"]), 4),
        "precision": round(float(report["precision"]), 4),
        "recall": round(float(report["recall"]), 4),
        "f1": round(float(report["f1"]), 4),
        "confusion": {k: report[k] for k in ("tp", "tn", "fp", "fn")},
        "adc_wet_mean": round(float(np.mean(adc_wet)), 1),
        "adc_dry_mean": round(float(np.mean(adc_dry)), 1),
        "adc_wet_samples": [round(float(x), 1) for x in adc_wet],
        "adc_dry_samples": [round(float(x), 1) for x in adc_dry],
        "drift": {
            "weeks": weeks,
            "drift_per_week_counts": drift_per_week,
            "accuracy_no_recal": [round(float(a), 4) for a in acc_no_recal],
            "accuracy_recal": [round(float(a), 4) for a in acc_recal],
        },
    }
