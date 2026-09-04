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


# ---- using the reconstruction itself -------------------------------------------------
def _truncated_binomial_q(view_counts: np.ndarray, detections: np.ndarray) -> float:
    """How reliable the detector is, given how many chances it had on each fruit.

    Each fruit had `c` clear views and was detected on `y` of them, so y is binomial in c
    with the detector's own hit rate q. Fruit detected on none of their chances are
    missing from the sample, so the likelihood is truncated at zero. Separating q from
    geometry this way is what makes both identifiable: the reconstruction says how many
    chances there were, and the histories say what was done with them.
    """

    def nll(q):
        q = float(np.clip(q, _P_FLOOR, _P_CEIL))
        ll = detections * np.log(q) + (view_counts - detections) * np.log1p(-q)
        ll -= np.log(np.maximum(1.0 - (1.0 - q) ** view_counts, _EPS))
        return -float(np.sum(ll))

    res = minimize_scalar(nll, bounds=(_P_FLOOR, _P_CEIL), method="bounded")
    return float(res.x)


def reconstruction_informed(observed: dict, n_bins: int = 8) -> float:
    """Estimate the total from measured observability rather than a smoothness assumption.

    Three steps. The reconstruction says how many cameras had a clear line to each
    detected fruit, which with the detection histories gives the detector's hit rate and
    therefore each fruit's chance of appearing at all. Reciprocal-probability weighting
    then recovers the fruit that were observable but missed. What remains is the fruit
    that were never observable, and those are estimated by taking the fruit density
    measured in each shell of the canopy and applying it to the unobserved part of that
    same shell.

    Working shell by shell matters. Fruit hang toward the outside of a canopy and the
    unobserved region is its middle, so assuming one density for the whole tree would
    put far too many fruit in the interior. Assuming instead that the observed and
    unobserved parts of a *given depth* hold fruit alike is a much weaker claim, and it
    is the one the geometry supports.

    In simulation the rays are traced against the true foliage, which is the sensing step
    rather than the estimating step. The estimator sees only what those rays returned. A
    real reconstruction carves free space with error, and that error is not modelled here.
    """
    if observed["n_views"] < MIN_VIEWS_FOR_DETECTION_MODEL:
        raise Unidentifiable("detection histories need at least two viewpoints")
    if "reconstruction" not in observed:
        raise Unidentifiable(
            "this estimator needs a reconstruction; scan with reconstruct_samples>0"
        )
    hist = observed["histories"]
    if len(hist) == 0:
        return 0.0
    scene = observed["reconstruction"]

    c = np.asarray(observed["fruit_view_counts"], float)
    y = hist.sum(axis=1).astype(float)
    c = np.maximum(c, y)  # a detection implies a clear view; guard sampling disagreement
    usable = c > 0
    if usable.sum() < 5:
        return float(len(hist))

    q = _truncated_binomial_q(c[usable], y[usable])
    pi = np.clip(1.0 - (1.0 - q) ** c[usable], _P_FLOOR, 1.0)
    weights = 1.0 / pi

    # Fruit density per shell, measured where the cameras could see.
    edges, shell_volume, shell_unknown = scene.radius_profile(n_bins)
    r = scene._normalised_radius(observed["positions"][usable])
    idx = np.clip(np.digitize(r, edges) - 1, 0, n_bins - 1)

    observed_volume = shell_volume * (1.0 - shell_unknown)
    density = np.full(n_bins, np.nan)
    for b in range(n_bins):
        sel = idx == b
        if sel.any() and observed_volume[b] > 1e-6:
            density[b] = weights[sel].sum() / observed_volume[b]

    known = ~np.isnan(density)
    if known.sum() < 2:
        return float(np.sum(weights))
    centres = 0.5 * (edges[:-1] + edges[1:])
    # Fruit thin out toward the centre; carry the measured trend into shells with no
    # observable volume rather than leaving them empty.
    coef = np.polyfit(centres[known], np.log(np.maximum(density[known], _EPS)), 1)
    filled = np.where(
        known, np.nan_to_num(density), np.exp(np.clip(np.polyval(coef, centres), -30, 30))
    )
    filled = np.minimum(filled, np.nanmax(density[known]))
    return float(np.sum(filled * shell_volume))


def _fit_density_profile(observed: dict, n_bins: int = 8):
    """Shared fitting step: detector hit rate, and fruit density by canopy shell."""
    scene = observed["reconstruction"]
    c = np.asarray(observed["fruit_view_counts"], float)
    y = observed["histories"].sum(axis=1).astype(float)
    c = np.maximum(c, y)
    usable = c > 0
    q = _truncated_binomial_q(c[usable], y[usable])
    pi = np.clip(1.0 - (1.0 - q) ** c[usable], _P_FLOOR, 1.0)
    weights = 1.0 / pi

    edges, shell_volume, shell_unknown = scene.radius_profile(n_bins)
    r = scene._normalised_radius(observed["positions"][usable])
    idx = np.clip(np.digitize(r, edges) - 1, 0, n_bins - 1)
    observed_volume = shell_volume * (1.0 - shell_unknown)
    density = np.full(n_bins, np.nan)
    for b in range(n_bins):
        sel = idx == b
        if sel.any() and observed_volume[b] > 1e-6:
            density[b] = weights[sel].sum() / observed_volume[b]
    return q, edges, shell_volume, density


def calibrate_interval_scale(
    trees, level: float = 0.90, n_boot: int = 80, seed: int = 0, n_bins: int = 8
) -> float:
    """Find the width multiplier that makes the stated coverage the achieved coverage.

    The parametric bootstrap gets the shape of the uncertainty roughly right and its size
    wrong, over-covering at 98% to 100% where it claims 90%. Rather than adjust the
    bootstrap until the number comes out, the raw interval is measured against trees whose
    totals are known and rescaled by one factor.

    For each calibration tree, the distance from the estimate to the truth is expressed in
    units of the raw half-width. The multiplier that would have covered the target share of
    those trees is that share's quantile of those distances, which is the same reasoning
    conformal prediction uses. It must be fitted on trees the coverage is not then reported
    on, or the number means nothing.
    """
    ratios = []
    for i, (observed, truth) in enumerate(trees):
        try:
            lo, hi = parametric_interval(observed, n_boot, level, seed + i, n_bins, scale=1.0)
        except Unidentifiable:
            continue
        half = (hi - lo) / 2.0
        if half <= 0:
            continue
        centre = (hi + lo) / 2.0
        ratios.append(abs(truth["n_fruit"] - centre) / half)
    if len(ratios) < 5:
        return 1.0
    return float(np.quantile(ratios, level))


def parametric_interval(
    observed: dict,
    n_boot: int = 150,
    level: float = 0.90,
    seed: int = 0,
    n_bins: int = 8,
    scale: float = 1.0,
) -> tuple[float, float]:
    """Interval from re-simulating the whole fitted model, not from reshuffling the fruit.

    The first attempt resampled the detected fruit and reported intervals that covered
    half of what they claimed (`FIX_LOG.md` entry 6). Resampling fruit varies which fruit
    this tree happened to grow and almost nothing else, while the uncertainty that
    actually dominates is in the fitted detector hit rate and the density carried into
    the unobserved region.

    So the whole chain is re-simulated. A synthetic tree is drawn with the estimated
    number of fruit, positioned by the estimated density profile, each fruit inheriting
    the clear-view count of the canopy point it sits at, and detected with the estimated
    hit rate. Re-estimating from each synthetic tree gives the spread the estimator
    actually has. Fruit that go undetected drop out exactly as they do in the real data,
    so the truncation is reproduced rather than assumed away.
    """
    if observed["n_views"] < MIN_VIEWS_FOR_DETECTION_MODEL or "reconstruction" not in observed:
        raise Unidentifiable("interval needs a reconstruction and at least two viewpoints")
    if len(observed["histories"]) == 0:
        return 0.0, 0.0

    rng = np.random.default_rng(seed)
    scene = observed["reconstruction"]
    q, edges, shell_volume, density = _fit_density_profile(observed, n_bins)
    known = ~np.isnan(density)
    if known.sum() < 2:
        raise Unidentifiable("too few observed shells to characterise the density profile")

    centres = 0.5 * (edges[:-1] + edges[1:])
    coef = np.polyfit(centres[known], np.log(np.maximum(density[known], _EPS)), 1)
    filled = np.where(
        known, np.nan_to_num(density), np.exp(np.clip(np.polyval(coef, centres), -30, 30))
    )
    filled = np.minimum(filled, np.nanmax(density[known]))
    n_hat = float(np.sum(filled * shell_volume))

    # Probability a fruit sits at each sampled canopy point, under the fitted profile.
    sample_bin = np.clip(np.digitize(scene.sample_radius, edges) - 1, 0, n_bins - 1)
    weight = filled[sample_bin]
    if weight.sum() <= 0:
        raise Unidentifiable("fitted density profile is degenerate")
    weight = weight / weight.sum()

    draws = []
    for _ in range(n_boot):
        n_sim = max(int(rng.poisson(n_hat)), 10)
        pick = rng.choice(len(scene.sample_points), size=n_sim, p=weight)
        c_sim = scene.sample_views[pick].astype(float)
        y_sim = rng.binomial(np.maximum(c_sim, 0).astype(int), q)
        keep = y_sim >= 1
        if keep.sum() < 10:
            continue
        hist = np.zeros((int(keep.sum()), observed["n_views"]), bool)
        for row, k in enumerate(np.flatnonzero(keep)):
            hist[row, : int(y_sim[k])] = True
        synthetic = {
            "positions": scene.sample_points[pick][keep],
            "histories": hist,
            "n_views": observed["n_views"],
            "params": observed["params"],
            "cameras": observed["cameras"],
            "reconstruction": scene,
            "fruit_view_counts": c_sim[keep],
        }
        try:
            draws.append(reconstruction_informed(synthetic, n_bins))
        except (Unidentifiable, np.linalg.LinAlgError, ValueError):
            continue
    if len(draws) < 20:
        raise Unidentifiable("parametric bootstrap did not produce enough usable draws")
    lo = float(np.percentile(draws, 100 * (1 - level) / 2))
    hi = float(np.percentile(draws, 100 * (1 + level) / 2))
    # Centre the spread on the point estimate rather than on the bootstrap median.
    median = float(np.median(draws))
    half = scale * (hi - lo) / 2.0
    centre = n_hat + ((lo + hi) / 2.0 - median)
    return centre - half, centre + half
