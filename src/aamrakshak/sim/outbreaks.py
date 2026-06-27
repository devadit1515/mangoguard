"""Independent outbreak-label generator (keeps the backtest honest).

The label is a noisy logistic of the TRUE weather, but deliberately a different
functional form and different coefficients from the Akem risk model under test:

- it uses morning RH *linearly*, not through the humid-thermal ratio;
- it weights leaf wetness and sunshine differently;
- it adds Bernoulli observation noise on top.

So a model that scores well against these labels is recovering a real signal,
not reading its own formula back. An outbreak == an anthracnose infection event
established at that block on that day.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Independent coefficients -- NOT the Akem coefficients.
OUTBREAK_COEFFS: dict[str, float] = {
    "intercept": -3.4,
    "rh_morning": 0.040,
    "leaf_wetness": 0.22,
    "temp_range": -0.06,
    "sunshine": -0.10,
}


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


def add_outbreak_labels(panel: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Add ``outbreak_prob`` and a Bernoulli ``outbreak`` column to the panel."""
    c = OUTBREAK_COEFFS
    temp_range = panel["t_max"] - panel["t_min"]
    z = (
        c["intercept"]
        + c["rh_morning"] * panel["rh_morning"]
        + c["leaf_wetness"] * panel["leaf_wetness_true"]
        + c["temp_range"] * temp_range
        + c["sunshine"] * panel["sunshine"]
    )
    prob = _sigmoid(z.to_numpy())
    rng = np.random.default_rng(seed + 11)
    out = panel.copy()
    out["outbreak_prob"] = prob
    out["outbreak"] = (rng.random(len(out)) < prob).astype(int)
    return out
