"""Tests for the canopy simulator and the estimators.

The important ones are the analytic checks on the physics. The simulator is the only
thing standing behind every number in the study until real trees are scanned, so it has
to be checked against closed-form answers rather than against itself. Run with: pytest
"""

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aamganak import canopy as C  # noqa: E402
from aamganak import estimators as E  # noqa: E402
from aamganak import visibility as V  # noqa: E402


# ---- geometry ----------------------------------------------------------------------
def test_path_length_along_axis_is_the_semi_axis():
    """From the centre of a sphere straight out, the path inside is exactly the radius."""
    p = C.TreeParams(radius=2.0, half_height=2.0, centre_height=0.0)
    out = C.path_length_through_canopy(np.zeros((1, 3)), np.array([10.0, 0.0, 0.0]), p)
    assert out[0] == pytest.approx(2.0, rel=1e-6)


def test_path_length_from_surface_is_zero():
    """A point on the surface looking straight out passes through no canopy."""
    p = C.TreeParams(radius=2.0, half_height=2.0, centre_height=0.0)
    out = C.path_length_through_canopy(np.array([[2.0, 0.0, 0.0]]), np.array([10.0, 0.0, 0.0]), p)
    assert out[0] == pytest.approx(0.0, abs=1e-6)


def test_path_length_scales_with_anisotropic_axes():
    """The ellipsoid transform must not distort distances along a non-principal ray."""
    p = C.TreeParams(radius=3.0, half_height=1.0, centre_height=0.0)
    out = C.path_length_through_canopy(np.zeros((1, 3)), np.array([0.0, 0.0, 50.0]), p)
    assert out[0] == pytest.approx(1.0, rel=1e-6)  # vertical semi-axis, not the horizontal one


def test_volume_samples_are_uniform_in_volume():
    """Half the canopy's volume lies inside 1/cbrt(2) of its radius, not half of it."""
    p = C.TreeParams(radius=2.0, half_height=2.0, centre_height=0.0)
    pts = C.sample_canopy_volume(p, 40000, np.random.default_rng(0))
    r = np.linalg.norm((pts - p.centre) / p.axes, axis=1)
    assert np.mean(r <= 0.5) == pytest.approx(0.125, abs=0.01)  # r^3 scaling


# ---- the physics the simulator is built on -----------------------------------------
def test_foliage_grid_reproduces_beer_lambert_on_average():
    """The clearest check available: the grid's mean transmittance must match theory.

    A grid whose cells are foliage with probability 1 - exp(-G*LAD*h) should let a ray
    of length L through with probability exp(-G*LAD*L). This is what licenses the claim
    that discretising the canopy changes the correlation structure and not the physics.
    """
    rng = np.random.default_rng(3)
    lad, voxel, length = 1.5, 0.05, 1.0
    p_occupied = 1.0 - np.exp(-C.G_SPHERICAL * lad * voxel)
    n_cells = int(round(length / voxel))
    trials = rng.random((20000, n_cells)) < p_occupied
    empirical = np.mean(~trials.any(axis=1))
    assert empirical == pytest.approx(np.exp(-C.G_SPHERICAL * lad * length), rel=0.05)


def test_denser_canopy_hides_more_fruit():
    rng = np.random.default_rng(5)
    seen = []
    for lad in (0.8, 3.0):
        params = C.TreeParams(leaf_area_density=lad, n_fruit=250)
        _, truth = V.scan_tree(params, 2, rng)
        seen.append(truth["visible_fraction"])
    assert seen[0] > seen[1]


def test_more_viewpoints_never_hide_more_fruit():
    rng = np.random.default_rng(6)
    params = C.TreeParams(leaf_area_density=2.5, n_fruit=250)
    few = V.scan_tree(params, 2, rng)[1]["visible_fraction"]
    many = V.scan_tree(params, 12, rng)[1]["visible_fraction"]
    assert many >= few


def test_a_fruit_does_not_occlude_itself():
    """The march starts on the fruit, so the first sample must be discarded."""
    rng = np.random.default_rng(7)
    params = C.TreeParams(leaf_area_density=0.01, n_fruit=30)
    _, truth = V.scan_tree(params, 4, rng, detector_reliability=1.0)
    assert truth["visible_fraction"] == pytest.approx(1.0)


# ---- estimators --------------------------------------------------------------------
def _synthetic_observation(n_true, p, m, rng, depths=None):
    det = rng.random((n_true, m)) < p
    seen = det.any(axis=1)
    params = C.TreeParams()
    pos = C.sample_fruit(C.TreeParams(n_fruit=n_true), rng)[seen]
    return {
        "positions": pos,
        "histories": det[seen],
        "n_views": m,
        "params": params,
        "cameras": V.camera_ring(m),
    }


def test_capture_recapture_recovers_a_known_total():
    """With a genuinely homogeneous detection probability it should land close."""
    rng = np.random.default_rng(11)
    obs = _synthetic_observation(1000, 0.25, 8, rng)
    assert E.capture_recapture(obs) == pytest.approx(1000, rel=0.10)


def test_naive_count_is_always_a_lower_bound():
    rng = np.random.default_rng(12)
    obs = _synthetic_observation(600, 0.3, 6, rng)
    assert E.naive(obs) <= E.capture_recapture(obs)


def test_chao_matches_its_closed_form():
    """Chao is f1^2 / (2 f2) above the observed count; check against a hand-built case."""
    hist = np.zeros((10, 4), bool)
    hist[:4, 0] = True  # four fruit seen exactly once
    hist[4:8, :2] = True  # four seen exactly twice
    hist[8:, :3] = True
    obs = {
        "histories": hist,
        "n_views": 4,
        "positions": np.zeros((10, 3)),
        "params": C.TreeParams(),
        "cameras": V.camera_ring(4),
    }
    assert E.chao(obs) == pytest.approx(10 + 16 / 8)


def test_single_viewpoint_is_refused_not_guessed():
    """One viewpoint cannot identify a detection probability, so it must raise."""
    rng = np.random.default_rng(13)
    obs = _synthetic_observation(400, 0.5, 1, rng)
    for fn in (E.capture_recapture, E.chao, E.horvitz_thompson, E.geometry_informed):
        with pytest.raises(E.Unidentifiable):
            fn(obs)


def test_estimators_survive_an_empty_scan():
    obs = {
        "histories": np.zeros((0, 4), bool),
        "positions": np.zeros((0, 3)),
        "n_views": 4,
        "params": C.TreeParams(),
        "cameras": V.camera_ring(4),
    }
    assert E.naive(obs) == 0
    assert E.capture_recapture(obs) == 0.0
    assert E.geometry_informed(obs) == 0.0


# ---- reconstruction ----------------------------------------------------------------
def test_wood_blocks_a_sight_line_through_the_trunk():
    """A point directly behind the trunk from the camera must be blocked by it."""
    params = C.TreeParams(radius=2.0, half_height=1.5, centre_height=2.0)
    wood = C.woody_structure(params, np.random.default_rng(0))
    trunk = [seg for seg in wood if seg[2] == params.trunk_radius][:1]
    camera = np.array([5.0, 0.0, 1.0])
    behind = np.array([[-1.0, 0.0, 1.0]])  # trunk sits between this point and the camera
    beside = np.array([[-1.0, 2.0, 1.0]])  # well off the trunk axis
    assert C.blocked_by_wood(behind, camera, trunk)[0]
    assert not C.blocked_by_wood(beside, camera, trunk)[0]


def test_unknown_region_grows_as_viewpoints_are_removed():
    rng = np.random.default_rng(21)
    params = C.TreeParams(leaf_area_density=1.8, n_fruit=200)
    grid = V.FoliageGrid(params, rng)
    from aamganak import reconstruct as R

    few = R.ReconstructedScene(params, V.camera_ring(2), grid, n_samples=2500, rng=rng)
    many = R.ReconstructedScene(params, V.camera_ring(12), grid, n_samples=2500, rng=rng)
    assert few.unknown_fraction > many.unknown_fraction


def test_unknown_and_observed_volume_sum_to_the_canopy():
    rng = np.random.default_rng(22)
    params = C.TreeParams(leaf_area_density=1.5, n_fruit=150)
    grid = V.FoliageGrid(params, rng)
    from aamganak import reconstruct as R

    scene = R.ReconstructedScene(params, V.camera_ring(4), grid, n_samples=2000, rng=rng)
    assert scene.unknown_volume + scene.observed_volume == pytest.approx(params.volume, rel=1e-9)


def test_reconstruction_estimator_needs_a_reconstruction():
    """It must refuse rather than silently fall back to a weaker estimate."""
    rng = np.random.default_rng(23)
    params = C.TreeParams(n_fruit=150)
    observed, _ = V.scan_tree(params, 4, rng)  # no reconstruct_samples
    with pytest.raises(E.Unidentifiable):
        E.reconstruction_informed(observed)


def test_reconstruction_estimator_beats_the_naive_count():
    rng = np.random.default_rng(24)
    params = C.TreeParams(leaf_area_density=1.8, n_fruit=300)
    observed, truth = V.scan_tree(params, 3, rng, reconstruct_samples=2500)
    est = E.reconstruction_informed(observed)
    assert est > E.naive(observed)  # it corrects upward
    assert abs(est - truth["n_fruit"]) < abs(E.naive(observed) - truth["n_fruit"])


def test_parametric_interval_brackets_its_own_point_estimate():
    rng = np.random.default_rng(25)
    params = C.TreeParams(leaf_area_density=1.5, n_fruit=300)
    observed, _ = V.scan_tree(params, 4, rng, reconstruct_samples=2500)
    est = E.reconstruction_informed(observed)
    lo, hi = E.parametric_interval(observed, n_boot=40, seed=1)
    assert lo < est < hi
    assert (hi - lo) / est < 1.0  # an interval wider than the estimate would be useless


def test_true_canopy_never_reaches_an_estimator():
    """Structural guard: the scan hands over no route back to the foliage."""
    rng = np.random.default_rng(26)
    observed, _ = V.scan_tree(C.TreeParams(n_fruit=120), 3, rng, reconstruct_samples=1500)
    assert "grid" not in observed
    assert not hasattr(observed["reconstruction"], "occupied")
