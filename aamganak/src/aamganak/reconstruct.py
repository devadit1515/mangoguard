"""What a three-dimensional reconstruction of the tree actually recovers.

The estimators up to this point used a smooth proxy for how deep a fruit sits: the mean
length of canopy between it and the cameras, computed from the canopy envelope. That
proxy assumes foliage is spread evenly, which is exactly the assumption the clumped
simulator was built to break. A real reconstruction does better, and this module models
what it recovers.

Photogrammetry and space carving do not measure density. They measure **where the camera
could see**, by carving out the space along every unobstructed line of sight. That splits
the canopy into three parts, and the third is the one that matters:

* **free** - some camera saw through this point, so anything there would have been visible
* **occupied** - a camera's line of sight terminated here, so there is something solid
* **unknown** - no camera ever saw this point, so nothing whatever is known about it

A fruit in the unknown region leaves no trace in any image and no trace in the detection
histories. It is invisible to statistics. But the *volume* of the unknown region is
measured, not assumed, and that is what makes the hidden fruit estimable at all.

Nothing here uses the true fruit positions or the true count. It uses the cameras and what
their rays did, which is what a reconstruction has.
"""

from __future__ import annotations

import numpy as np

from . import canopy as C
from . import visibility as V

_CHUNK = 2000  # points per ray-marching batch, to bound peak memory


def clear_view_counts(
    points: np.ndarray,
    cameras: np.ndarray,
    grid: V.FoliageGrid,
    fruit: np.ndarray | None = None,
    fruit_radius: float = 0.0,
) -> np.ndarray:
    """(n_points,) how many cameras have an unobstructed line of sight to each point.

    This is the quantity a carved reconstruction gives for any point in space, and it is
    the honest replacement for the canopy-depth proxy. Zero means the point was never
    observed from anywhere, which is the definition of the unknown region.
    """
    points = np.atleast_2d(points)
    counts = np.zeros(len(points), int)
    for start in range(0, len(points), _CHUNK):
        block = points[start : start + _CHUNK]
        for cam in cameras:
            clear = ~grid.blocked(block, cam)
            if fruit is not None and fruit_radius > 0:
                clear &= ~_blocked_by_fruit(block, fruit, cam, fruit_radius)
            counts[start : start + _CHUNK] += clear
    return counts


def _blocked_by_fruit(
    points: np.ndarray, fruit: np.ndarray, camera: np.ndarray, radius: float
) -> np.ndarray:
    """Whether any fruit sits on the line from each point to the camera."""
    to_cam = np.asarray(camera, float) - points
    seg_len = np.linalg.norm(to_cam, axis=1, keepdims=True)
    direction = to_cam / np.maximum(seg_len, 1e-12)
    v = fruit[None, :, :] - points[:, None, :]
    t = np.einsum("ikd,id->ik", v, direction)
    perp = np.linalg.norm(v - t[:, :, None] * direction[:, None, :], axis=2)
    # A point is not occluded by a fruit sitting essentially on top of it (itself).
    return ((t > radius) & (t < seg_len) & (perp < radius)).any(axis=1)


class ReconstructedScene:
    """The canopy as the cameras managed to see it.

    Holds a Monte Carlo sample of the canopy volume, each sample point labelled with how
    many cameras could see it. From that follow the two numbers the estimator needs: the
    volume that was never observed, and how observability varies with position.

    Sampling the volume rather than filling a grid is deliberate. The quantities wanted
    are integrals over the canopy, a sample estimates them without the cost of carving
    half a million cells, and the sampling error is reportable.
    """

    def __init__(
        self,
        params: C.TreeParams,
        cameras: np.ndarray,
        grid: V.FoliageGrid,
        fruit: np.ndarray | None = None,
        n_samples: int = 12000,
        rng: np.random.Generator | None = None,
    ):
        rng = rng or np.random.default_rng(0)
        self.params = params
        self.cameras = cameras
        self.n_views = len(cameras)
        self.sample_points = C.sample_canopy_volume(params, n_samples, rng)
        self.sample_views = clear_view_counts(
            self.sample_points,
            cameras,
            grid,
            fruit,
            params.fruit_radius if fruit is not None else 0.0,
        )
        self.sample_radius = self._normalised_radius(self.sample_points)

    def _normalised_radius(self, points: np.ndarray) -> np.ndarray:
        """Position in the canopy as a fraction of the way from centre to skin."""
        return np.linalg.norm(
            (np.atleast_2d(points) - self.params.centre) / self.params.axes, axis=1
        )

    @property
    def unknown_fraction(self) -> float:
        """Share of the canopy volume no camera ever saw into."""
        return float(np.mean(self.sample_views == 0))

    @property
    def unknown_volume(self) -> float:
        return self.unknown_fraction * self.params.volume

    @property
    def observed_volume(self) -> float:
        return (1.0 - self.unknown_fraction) * self.params.volume

    def fruit_view_counts(self, fruit_positions: np.ndarray, grid: V.FoliageGrid) -> np.ndarray:
        """How many cameras had a clear line to each detected fruit.

        Other fruit block lines of sight as surely as leaves do, so they are included as
        occluders. Only the *detected* fruit can play that role, because a reconstruction
        does not know about the ones it missed. That undercounts occlusion slightly, and
        the direction is worth naming: it inflates the estimated number of chances the
        detector had, which pushes the detector's estimated hit rate down and the final
        count up.
        """
        return clear_view_counts(
            fruit_positions,
            self.cameras,
            grid,
            fruit=fruit_positions if len(fruit_positions) > 1 else None,
            fruit_radius=self.params.fruit_radius,
        )

    def radius_profile(self, n_bins: int = 10):
        """Canopy volume and mean observability, in shells from centre to skin.

        Returns bin edges, the volume in each shell, and the fraction of each shell that
        was never observed. Integrating a fruit-density profile against these shells is
        how the unknown region gets its estimate.
        """
        edges = np.linspace(0.0, 1.0, n_bins + 1)
        idx = np.clip(np.digitize(self.sample_radius, edges) - 1, 0, n_bins - 1)
        volume = np.zeros(n_bins)
        unknown = np.zeros(n_bins)
        for b in range(n_bins):
            sel = idx == b
            volume[b] = self.params.volume * float(np.mean(sel))
            unknown[b] = float(np.mean(self.sample_views[sel] == 0)) if sel.any() else 1.0
        return edges, volume, unknown


def reconstruct(observed: dict, grid: V.FoliageGrid, n_samples: int = 12000, seed: int = 0):
    """Build the reconstruction a pipeline would produce for one scanned tree."""
    return ReconstructedScene(
        observed["params"],
        observed["cameras"],
        grid,
        fruit=observed["positions"] if len(observed["positions"]) else None,
        n_samples=n_samples,
        rng=np.random.default_rng(seed),
    )
