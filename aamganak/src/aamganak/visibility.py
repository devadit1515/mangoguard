"""What each camera position can and cannot see, and the detections that result.

A phone walked around a tree gives a set of viewpoints. For every fruit and every
viewpoint there are three separate reasons the fruit might not be counted: foliage in
the way, another fruit in the way, or a detector that misses a fruit it could have
seen. They are kept apart because they behave differently.

**The foliage is a fixed object, not a probability.** An earlier version of this module
drew each viewpoint's occlusion independently from the Beer-Lambert transmittance for
that line of sight. That is wrong, and wrong in the direction that flatters the whole
project: leaves do not rearrange themselves between viewpoints, so a fruit hidden from
one direction is usually hidden from the neighbouring direction too. Independent draws
turned a 30% per-view chance into a 99% chance of being seen at least once over twelve
views, and 86% of fruit came out visible. Real canopies hide far more than that.

So the canopy is built once per tree as a grid of cells that are either foliage or air,
with the occupancy set so that the *average* transmittance still matches Beer-Lambert,
and every line of sight is traced through that one fixed realisation. Fruit deep inside
a dense canopy are then invisible from every direction, which is the situation the whole
project exists to handle.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter

from . import canopy as C

VOXEL_SIZE = 0.05  # 5 cm cells, roughly the scale of a mango leaf
CLUMP_SCALE = 0.20  # metres; leaves grow in shoots, not as independent specks
_MARCH_STEPS = 256


def camera_ring(
    n_views: int, radius: float = 4.0, height: float = 1.6, centre_height: float = 2.4
) -> np.ndarray:
    """(n_views, 3) camera positions evenly spaced on a circle around the tree.

    A person walking a full lap of a tree holding a phone at chest height. The radius is
    the standing distance from the trunk, not from the canopy edge.
    """
    angles = np.linspace(0.0, 2.0 * np.pi, n_views, endpoint=False)
    return np.column_stack(
        [radius * np.cos(angles), radius * np.sin(angles), np.full(n_views, height)]
    )


class FoliageGrid:
    """One fixed realisation of a canopy's foliage, as occupied or empty cells.

    The fraction of cells that hold foliage is p = 1 - exp(-G * LAD * h), which is the
    value that reproduces Beer-Lambert attenuation on average for scattered foliage.

    Those cells are then clumped rather than sprinkled. Leaves grow in shoots and shoots
    grow on branches, so foliage in a real canopy is spatially correlated over roughly
    20 cm, and canopy radiative-transfer models carry a clumping index precisely because
    scattered-leaf theory gets gap statistics wrong without it. Clumping is imposed here
    by smoothing a random field and thresholding it at the target occupancy, which keeps
    the density identical and changes only how it is arranged. The consequence matters:
    clumped foliage leaves larger persistent gaps in some directions and denser
    persistent shadow in others, so which fruit are hidden becomes a property of where
    they sit rather than of luck.
    """

    def __init__(
        self,
        params: C.TreeParams,
        rng: np.random.Generator,
        voxel: float = VOXEL_SIZE,
        clump_scale: float = CLUMP_SCALE,
    ):
        self.params = params
        self.wood = C.woody_structure(params, rng)
        self.voxel = voxel
        self.lower = params.centre - params.axes
        extent = 2.0 * params.axes
        self.shape = np.maximum(np.ceil(extent / voxel).astype(int), 1)

        p_occupied = 1.0 - np.exp(-C.G_SPHERICAL * params.leaf_area_density * voxel)
        field = gaussian_filter(rng.normal(size=tuple(self.shape)), clump_scale / voxel)
        occupied = field >= np.quantile(field, 1.0 - p_occupied)

        # Foliage only exists inside the canopy envelope.
        idx = np.indices(self.shape).reshape(3, -1).T
        centres = self.lower + (idx + 0.5) * voxel
        inside = np.sum(((centres - params.centre) / params.axes) ** 2, axis=1) <= 1.0
        self.occupied = occupied & inside.reshape(self.shape)

    def blocked(self, starts: np.ndarray, camera: np.ndarray) -> np.ndarray:
        """Boolean per start point: does foliage interrupt the line to this camera?

        The ray is clipped to the canopy before marching. Most of the distance from a
        fruit to a camera is open air outside the tree, and spending sample points there
        left the steps coarser than the cells they were meant to test, so thin foliage
        could be stepped straight over. Marching only the part inside the canopy puts
        every sample where it can matter and keeps the step below half a cell.
        """
        starts = np.atleast_2d(starts)
        cam = np.asarray(camera, float)
        exit_frac = self._canopy_exit_fraction(starts, cam)
        t = np.linspace(0.0, 1.0, _MARCH_STEPS)[None, :, None] * exit_frac[:, None, None]
        pts = starts[:, None, :] + t * (cam - starts)[:, None, :]
        ijk = np.floor((pts - self.lower) / self.voxel).astype(int)
        valid = np.all((ijk >= 0) & (ijk < self.shape), axis=2)
        ijk = np.clip(ijk, 0, self.shape - 1)
        hit = self.occupied[ijk[..., 0], ijk[..., 1], ijk[..., 2]] & valid
        # The first step sits on the fruit itself; ignore it so a fruit cannot occlude itself.
        leaves = hit[:, 1:].any(axis=1)
        return leaves | C.blocked_by_wood(starts, cam, self.wood)

    def _canopy_exit_fraction(self, starts: np.ndarray, camera: np.ndarray) -> np.ndarray:
        """Fraction of the fruit-to-camera segment that lies inside the canopy envelope."""
        params = self.params
        p = (starts - params.centre) / params.axes
        q = (camera - params.centre) / params.axes
        d = q - p
        a = np.sum(d * d, axis=1)
        b = 2.0 * np.sum(p * d, axis=1)
        c = np.sum(p * p, axis=1) - 1.0
        disc = np.maximum(b * b - 4.0 * a * c, 0.0)
        t_exit = (-b + np.sqrt(disc)) / (2.0 * a)
        return np.clip(t_exit, 1e-6, 1.0)


def mean_path_length(points: np.ndarray, cameras: np.ndarray, params: C.TreeParams) -> np.ndarray:
    """Average canopy depth each point sits behind, over all viewpoints.

    This is the covariate the estimator is allowed to use, because a 3D reconstruction
    yields the fruit positions and the canopy envelope, and therefore this number,
    without knowing the foliage density or the true count.
    """
    points = np.atleast_2d(points)
    total = np.zeros(len(points))
    for cam in cameras:
        total += C.path_length_through_canopy(points, cam, params)
    return total / len(cameras)


def _blocked_by_other_fruit(
    fruit: np.ndarray, camera: np.ndarray, fruit_radius: float
) -> np.ndarray:
    """Boolean per fruit: does another fruit sit on the line to this camera?"""
    n = len(fruit)
    if n < 2:
        return np.zeros(n, bool)
    to_cam = np.asarray(camera, float) - fruit
    seg_len = np.linalg.norm(to_cam, axis=1, keepdims=True)
    direction = to_cam / seg_len

    v = fruit[None, :, :] - fruit[:, None, :]
    t = np.einsum("ikd,id->ik", v, direction)
    perp = v - t[:, :, None] * direction[:, None, :]
    perp_dist = np.linalg.norm(perp, axis=2)

    occludes = (t > 0.0) & (t < seg_len) & (perp_dist < fruit_radius)
    np.fill_diagonal(occludes, False)
    return occludes.any(axis=1)


def detection_histories(
    fruit: np.ndarray,
    cameras: np.ndarray,
    params: C.TreeParams,
    grid: FoliageGrid,
    detector_reliability: float = 0.95,
    rng: np.random.Generator | None = None,
):
    """Simulate one scan of one tree against a fixed foliage realisation.

    Returns the detection matrix (n_fruit, n_views) and the clear-line-of-sight matrix,
    which the study reports on but no estimator is allowed to see.
    """
    rng = rng or np.random.default_rng()
    n, m = len(fruit), len(cameras)
    clear = np.zeros((n, m), bool)
    for j, cam in enumerate(cameras):
        clear[:, j] = ~grid.blocked(fruit, cam) & ~_blocked_by_other_fruit(
            fruit, cam, params.fruit_radius
        )
    detections = clear & (rng.random((n, m)) < detector_reliability)
    return detections, clear


def scan_tree(
    params: C.TreeParams,
    n_views: int,
    rng: np.random.Generator,
    detector_reliability: float = 0.95,
    camera_radius: float = 4.0,
    reconstruct_samples: int = 0,
):
    """One simulated tree, scanned once. Everything downstream starts here.

    The `observed` dictionary holds exactly what a real pipeline recovers from the video:
    the positions of the fruit detected at least once, which viewpoints saw each of them,
    and the canopy envelope. The true count is returned separately for scoring and must
    never be passed to an estimator.
    """
    fruit = C.sample_fruit(params, rng)
    cameras = camera_ring(n_views, radius=camera_radius, centre_height=params.centre_height)
    grid = FoliageGrid(params, rng)
    detections, clear = detection_histories(fruit, cameras, params, grid, detector_reliability, rng)

    seen = detections.any(axis=1)
    observed = {
        "positions": fruit[seen],
        "histories": detections[seen],
        "n_views": n_views,
        "params": params,
        "cameras": cameras,
    }
    if reconstruct_samples:
        # Everything a carved reconstruction would recover is computed here, at sensing
        # time, and only the results are handed on. The foliage itself never enters the
        # dictionary an estimator receives, so no estimator can reach the true canopy
        # even by accident. The guard is structural rather than a matter of discipline.
        from . import reconstruct as R

        scene = R.ReconstructedScene(
            params,
            cameras,
            grid,
            fruit=observed["positions"] if len(observed["positions"]) > 1 else None,
            n_samples=reconstruct_samples,
            rng=rng,
        )
        observed["reconstruction"] = scene
        observed["fruit_view_counts"] = (
            scene.fruit_view_counts(observed["positions"], grid)
            if len(observed["positions"])
            else np.zeros(0, int)
        )
    truth = {
        "n_fruit": params.n_fruit,
        "n_seen": int(seen.sum()),
        "visible_fraction": float(seen.mean()),
        "never_visible_fraction": float((~clear.any(axis=1)).mean()),
    }
    return observed, truth
