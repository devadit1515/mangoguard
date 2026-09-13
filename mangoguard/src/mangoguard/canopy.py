"""Mango tree canopies with a known fruit count.

The estimator has to be judged against a truth, and on a real tree the truth costs a
harvest to obtain. So the development loop runs on simulated trees where the total is
known by construction, and the real orchard is kept for the final test rather than
spent on debugging.

A canopy here is an ellipsoid of foliage with a leaf area density, and the fruit are
points inside it. Mangoes hang mostly toward the outside of the canopy, on the current
season's growth, so the radial positions are drawn with a bias to the outer shell
rather than uniformly through the volume. Everything else about a tree that a camera
would care about follows from those two facts.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Leaf angle projection for a spherical leaf-angle distribution. Beer-Lambert
# attenuation through foliage uses G * LAD as the extinction coefficient, and G = 0.5
# is the standard value when leaves point in every direction equally.
G_SPHERICAL = 0.5


@dataclass(frozen=True)
class TreeParams:
    """One tree. Lengths in metres.

    `leaf_area_density` is one-sided leaf area per unit canopy volume, in m^2/m^3.
    Multiplying it by the canopy's vertical extent gives roughly the leaf area index,
    so a 3 m canopy at 1.5 m^-1 is an LAI near 4.5, which is an ordinary bearing mango.
    """

    radius: float = 2.2  # horizontal semi-axis
    half_height: float = 1.8  # vertical semi-axis
    centre_height: float = 2.4  # canopy centre above ground
    leaf_area_density: float = 1.5
    n_fruit: int = 300
    fruit_radius: float = 0.05  # a mango is roughly 100 mm across
    shell_alpha: float = 3.0  # Beta shape for normalised radius: mean = a/(a+b)
    shell_beta: float = 2.0
    trunk_radius: float = 0.14  # a mature mango trunk
    n_branches: int = 7  # primary scaffold limbs
    branch_radius: float = 0.055

    @property
    def axes(self) -> np.ndarray:
        return np.array([self.radius, self.radius, self.half_height], float)

    @property
    def centre(self) -> np.ndarray:
        return np.array([0.0, 0.0, self.centre_height], float)

    @property
    def volume(self) -> float:
        a, b, c = self.axes
        return 4.0 / 3.0 * np.pi * a * b * c


def _unit_ball_shell(n: int, alpha: float, beta: float, rng: np.random.Generator):
    """n points in the unit ball, radially biased toward the surface."""
    direction = rng.normal(size=(n, 3))
    direction /= np.linalg.norm(direction, axis=1, keepdims=True)
    r = rng.beta(alpha, beta, size=n)[:, None]
    return direction * r


def sample_fruit(params: TreeParams, rng: np.random.Generator) -> np.ndarray:
    """(n_fruit, 3) fruit centres in world coordinates."""
    return (
        params.centre
        + _unit_ball_shell(params.n_fruit, params.shell_alpha, params.shell_beta, rng) * params.axes
    )


def sample_canopy_volume(params: TreeParams, n: int, rng: np.random.Generator) -> np.ndarray:
    """(n, 3) points drawn uniformly through the canopy volume.

    Used to measure how much canopy sits at each viewing depth, which is what lets the
    estimator reason about the part of the tree no camera could see into.
    """
    direction = rng.normal(size=(n, 3))
    direction /= np.linalg.norm(direction, axis=1, keepdims=True)
    r = rng.uniform(size=n)[:, None] ** (1.0 / 3.0)  # uniform in volume, not in radius
    return params.centre + direction * r * params.axes


def path_length_through_canopy(
    points: np.ndarray, camera: np.ndarray, params: TreeParams
) -> np.ndarray:
    """Distance, in metres, that the line from each point to the camera spends inside the canopy.

    The ellipsoid becomes a unit sphere under division by its semi-axes, and the ray's
    parameter along the segment is unchanged by that scaling, so the interval inside is
    found in sphere coordinates and converted back by the segment's true length.
    """
    points = np.atleast_2d(points)
    p = (points - params.centre) / params.axes
    q = (np.asarray(camera, float) - params.centre) / params.axes
    d = q - p
    seg_len = np.linalg.norm(np.asarray(camera, float) - points, axis=1)

    a = np.sum(d * d, axis=1)
    b = 2.0 * np.sum(p * d, axis=1)
    c = np.sum(p * p, axis=1) - 1.0
    disc = b * b - 4.0 * a * c

    out = np.zeros(len(points))
    hit = disc > 0
    if not np.any(hit):
        return out
    sq = np.sqrt(disc[hit])
    t0 = (-b[hit] - sq) / (2.0 * a[hit])
    t1 = (-b[hit] + sq) / (2.0 * a[hit])
    # The fruit sits inside the canopy, so the interval of interest runs from the fruit
    # (t = 0) to wherever the ray leaves the ellipsoid, clipped to the segment.
    lo = np.clip(np.minimum(t0, t1), 0.0, 1.0)
    hi = np.clip(np.maximum(t0, t1), 0.0, 1.0)
    out[hit] = np.maximum(hi - lo, 0.0) * seg_len[hit]
    return out


def foliage_transmittance(path_len: np.ndarray, leaf_area_density: float) -> np.ndarray:
    """Probability that a line of sight of this length through foliage is unobstructed.

    Beer-Lambert: each metre of canopy presents G * LAD of leaf area per unit volume,
    and the chance of threading through without meeting a leaf falls exponentially.
    """
    return np.exp(-G_SPHERICAL * leaf_area_density * np.asarray(path_len, float))


def woody_structure(params: TreeParams, rng: np.random.Generator):
    """Trunk and primary scaffold limbs, as opaque capsules.

    Leaves are not the only thing between a camera and a fruit. A mature mango carries a
    trunk of roughly 280 mm diameter and a handful of primary limbs, and those block a
    line of sight completely rather than probabilistically. Leaving them out was why the
    simulator reported far more visible fruit than the field measures: compensating with
    leaf density instead would have needed a leaf area index above 20, against the 3 to 6
    a real bearing mango carries, which is how I know the missing occluder was wood
    rather than foliage.

    Returned as (start, end, radius) segments in world coordinates.
    """
    centre, axes = params.centre, params.axes
    base = np.array([0.0, 0.0, 0.0])
    fork = np.array([0.0, 0.0, centre[2] - 0.35 * axes[2]])
    segments = [(base, fork, params.trunk_radius)]
    angles = rng.permutation(np.linspace(0, 2 * np.pi, params.n_branches, endpoint=False))
    for k, ang in enumerate(angles):
        reach = 0.55 + 0.35 * rng.random()
        tip = centre + np.array(
            [
                reach * axes[0] * np.cos(ang),
                reach * axes[1] * np.sin(ang),
                axes[2] * (0.55 * (k % 3 - 1) + 0.2 * rng.standard_normal()),
            ]
        )
        segments.append((fork, tip, params.branch_radius))
    return segments


def blocked_by_wood(points: np.ndarray, camera: np.ndarray, segments) -> np.ndarray:
    """Whether the line from each point to the camera passes through trunk or limb."""
    points = np.atleast_2d(points)
    cam = np.asarray(camera, float)
    blocked = np.zeros(len(points), bool)
    d = cam - points
    seg_len = np.linalg.norm(d, axis=1, keepdims=True)
    direction = d / np.maximum(seg_len, 1e-12)
    for a, b, radius in segments:
        ab = b - a
        ab_len2 = float(ab @ ab)
        if ab_len2 < 1e-12:
            continue
        # Closest approach between the sight line and the limb axis, sampled along the
        # limb. Sampling rather than solving keeps the capsule ends handled correctly.
        for t in np.linspace(0.0, 1.0, 12):
            axis_pt = a + t * ab
            v = axis_pt - points
            proj = np.einsum("id,id->i", v, direction)
            perp = np.linalg.norm(v - proj[:, None] * direction, axis=1)
            blocked |= (proj > 0) & (proj < seg_len[:, 0]) & (perp < radius)
    return blocked
