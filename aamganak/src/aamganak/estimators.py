"""Turning the fruit a camera saw into the fruit a tree carries.

Four families, in increasing order of what they use.

*Naive* counts the detections and stops. *Fixed multiplier* scales that count by a
constant fitted on other trees, which is what published fruit-counting work does.
*Capture-recapture* uses the pattern of which viewpoints saw which fruit: a fruit seen
from two viewpoints out of twelve is evidence that fruit like it are easy to miss, and
the frequency distribution of those sightings implies how many were missed entirely.
*Geometry-informed* adds the one thing capture-recapture structurally cannot recover.

That last point is the reason the project exists. Capture-recapture infers the unseen
from the barely-seen, so it needs every fruit to have some chance of being seen. A
mango deep inside a dense canopy has, to several decimal places, no chance of being
seen from anywhere on a walk around the tree. It leaves no trace in the detection
histories at all, and no estimator working from those histories alone can know it is
there. What does know is the shape of the canopy: a reconstruction measures how much
volume sits behind more foliage than any camera could see through, and the fruit
density in the parts that were observable says roughly what is likely to be in it.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize, minimize_scalar

from . import visibility as V

_EPS = 1e-9
_P_FLOOR, _P_CEIL = 1e-6, 1.0 - 1e-6
MIN_VIEWS_FOR_DETECTION_MODEL = 2


class Unidentifiable(ValueError):
    """Raised when the data cannot support the estimator at all.

    With a single viewpoint every observed fruit has been seen exactly once, so the
    distribution of sighting counts is a single point and carries no information about
    how many fruit were missed. The detection probability is not merely hard to
    estimate, it is not identified, and any number returned would be an artefact of the
    optimiser rather than a measurement. Refusing is the correct behaviour.
    """


def _inclusion_prob(p: np.ndarray, m: int) -> np.ndarray:
    """Probability a fruit with per-view detection probability p is seen at least once."""
    return 1.0 - (1.0 - np.clip(p, _P_FLOOR, _P_CEIL)) ** m


def naive(observed: dict) -> float:
    """Count what was detected. The floor every other estimator has to beat."""
    return float(len(observed["histories"]))


def fixed_multiplier(observed: dict, k: float) -> float:
    """The field's current practice: scale the visible count by a calibrated constant."""
    return naive(observed) * k


def fit_multiplier(training: list[tuple[dict, dict]]) -> float:
    """Fit that constant the way it is fitted in practice, on trees with known totals."""
    ratios = [t["n_fruit"] / max(len(o["histories"]), 1) for o, t in training]
    return float(np.mean(ratios))


# ---- capture-recapture -------------------------------------------------------------
def _truncated_binomial_nll(p: float, counts: np.ndarray, m: int) -> float:
    """Negative log-likelihood of sighting counts under a zero-truncated binomial.

    Truncated because fruit seen zero times are absent from the data by definition. The
    binomial coefficient does not depend on p, so it is dropped.
    """
    p = float(np.clip(p, _P_FLOOR, _P_CEIL))
    ll = counts * np.log(p) + (m - counts) * np.log1p(-p)
    ll -= np.log(max(1.0 - (1.0 - p) ** m, _EPS))
    return -float(np.sum(ll))


def capture_recapture(observed: dict) -> float:
    """Homogeneous capture-recapture: one detection probability shared by all fruit."""
    if observed["n_views"] < MIN_VIEWS_FOR_DETECTION_MODEL:
        raise Unidentifiable("detection histories need at least two viewpoints")
    hist = observed["histories"]
    m = observed["n_views"]
    if len(hist) == 0:
        return 0.0
    counts = hist.sum(axis=1).astype(float)
    res = minimize_scalar(
        _truncated_binomial_nll, bounds=(_P_FLOOR, _P_CEIL), args=(counts, m), method="bounded"
    )
    return float(len(hist) / _inclusion_prob(np.array([res.x]), m)[0])


def chao(observed: dict) -> float:
    """Chao's lower bound, which allows fruit to differ in how detectable they are.

    Built from the fruit seen exactly once and exactly twice: a sample full of
    seen-once fruit implies a large unseen population.
    """
    if observed["n_views"] < MIN_VIEWS_FOR_DETECTION_MODEL:
        raise Unidentifiable("detection histories need at least two viewpoints")
    hist = observed["histories"]
    if len(hist) == 0:
        return 0.0
    counts = hist.sum(axis=1)
    f1 = float(np.sum(counts == 1))
    f2 = float(np.sum(counts == 2))
    if f2 == 0:
        return float(len(hist) + f1 * (f1 - 1) / 2.0)  # bias-corrected form
    return float(len(hist) + f1 * f1 / (2.0 * f2))


# ---- detection model on canopy depth ------------------------------------------------
def _depths(observed: dict) -> np.ndarray:
    """Mean canopy depth behind each observed fruit, from the reconstruction geometry."""
    return V.mean_path_length(observed["positions"], observed["cameras"], observed["params"])


def _fit_depth_model(depths: np.ndarray, counts: np.ndarray, m: int) -> tuple[float, float]:
    """Zero-truncated binomial regression of sighting count on depth.

    logit(p) = a + b * depth. Fitted only on fruit that were seen, with the truncation
    correcting for the fact that unseen fruit are missing from the sample.
    """

    def nll(theta):
        a, b = theta
        z = np.clip(a + b * depths, -30.0, 30.0)
        p = np.clip(1.0 / (1.0 + np.exp(-z)), _P_FLOOR, _P_CEIL)
        ll = counts * np.log(p) + (m - counts) * np.log1p(-p)
        ll -= np.log(np.maximum(1.0 - (1.0 - p) ** m, _EPS))
        return -float(np.sum(ll))

    best = minimize(nll, x0=np.array([1.0, -1.0]), method="Nelder-Mead")
    return float(best.x[0]), float(best.x[1])


def _p_from_depth(depths: np.ndarray, a: float, b: float) -> np.ndarray:
    z = np.clip(a + b * np.asarray(depths, float), -30.0, 30.0)
    return np.clip(1.0 / (1.0 + np.exp(-z)), _P_FLOOR, _P_CEIL)


def horvitz_thompson(observed: dict) -> float:
    """Weight each detected fruit by the reciprocal of its chance of being detected.

    A fruit that had a one-in-four chance of appearing at all stands for four fruit.
    This recovers everything the detection histories can support, and stops exactly
    where they run out.
    """
    if observed["n_views"] < MIN_VIEWS_FOR_DETECTION_MODEL:
        raise Unidentifiable("detection histories need at least two viewpoints")
    hist = observed["histories"]
    m = observed["n_views"]
    if len(hist) == 0:
        return 0.0
    depths = _depths(observed)
    counts = hist.sum(axis=1).astype(float)
    a, b = _fit_depth_model(depths, counts, m)
    pi = _inclusion_prob(_p_from_depth(depths, a, b), m)
    return float(np.sum(1.0 / pi))


def geometry_informed(
    observed: dict,
    n_volume_samples: int = 20000,
    n_bins: int = 12,
    pi_reliable: float = 0.25,
    rng: np.random.Generator | None = None,
) -> float:
    """Horvitz-Thompson, extended into the canopy the cameras could not see into.

    The canopy is divided into shells of equal viewing depth. Within the shells that
    were well observed, the reciprocal-probability estimate gives a fruit density per
    cubic metre. Those densities describe how fruit thin out with depth, and that trend
    carries into the shells where detection was hopeless, whose volume the geometry
    supplies. The estimate is the density profile integrated over the whole canopy.
    """
    if observed["n_views"] < MIN_VIEWS_FOR_DETECTION_MODEL:
        raise Unidentifiable("detection histories need at least two viewpoints")
    hist = observed["histories"]
    m = observed["n_views"]
    params = observed["params"]
    if len(hist) == 0:
        return 0.0
    rng = rng or np.random.default_rng(0)

    depths = _depths(observed)
    counts = hist.sum(axis=1).astype(float)
    a, b = _fit_depth_model(depths, counts, m)

    # How the canopy's own volume is distributed over viewing depth.
    vol_pts = V.C.sample_canopy_volume(params, n_volume_samples, rng)
    vol_depths = V.mean_path_length(vol_pts, observed["cameras"], params)
    edges = np.linspace(0.0, max(vol_depths.max(), depths.max()) + _EPS, n_bins + 1)
    vol_hist, _ = np.histogram(vol_depths, bins=edges)
    bin_volume = params.volume * vol_hist / max(n_volume_samples, 1)
    centres = 0.5 * (edges[:-1] + edges[1:])

    pi_bin = _inclusion_prob(_p_from_depth(centres, a, b), m)
    obs_per_bin, _ = np.histogram(depths, bins=edges)

    reliable = (pi_bin >= pi_reliable) & (bin_volume > 0) & (obs_per_bin > 0)
    if reliable.sum() < 2:
        return horvitz_thompson(observed)

    density = np.zeros(n_bins)
    density[reliable] = (obs_per_bin[reliable] / pi_bin[reliable]) / bin_volume[reliable]

    # Fruit thin out with depth; fit that decline where it is measurable and carry it in.
    w = obs_per_bin[reliable].astype(float)
    coef = np.polyfit(centres[reliable], np.log(np.maximum(density[reliable], _EPS)), 1, w=w)
    predicted = np.exp(np.clip(np.polyval(coef, centres), -30.0, 30.0))
    predicted = np.minimum(predicted, density[reliable].max())

    filled = np.where(reliable, density, predicted)
    return float(np.sum(filled * bin_volume))


def bootstrap_interval(
    observed: dict, estimator, n_boot: int = 200, level: float = 0.90, seed: int = 0
) -> tuple[float, float]:
    """Percentile interval by resampling the detected fruit.

    Resampling fruit rather than viewpoints keeps the canopy geometry fixed and varies
    the thing that is actually a sample: which fruit this tree happened to grow where.
    """
    rng = np.random.default_rng(seed)
    n = len(observed["histories"])
    if n == 0:
        return 0.0, 0.0
    draws = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        resampled = dict(observed)
        resampled["histories"] = observed["histories"][idx]
        resampled["positions"] = observed["positions"][idx]
        draws.append(estimator(resampled))
    lo = float(np.percentile(draws, 100 * (1 - level) / 2))
    hi = float(np.percentile(draws, 100 * (1 + level) / 2))
    return lo, hi
