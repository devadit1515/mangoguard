"""Powdery mildew infection-risk model.

References
----------
NHB Technical Bulletin No. 31 (Mango: A Manual for Production Technology)
documents *Oidium mangiferae* infection thresholds at:

- Daily min temperature in [11, 14] degC
- Daily max temperature in [17, 31] degC
- Mean RH in [64, 72] percent

ICAR-CISH forewarning bulletins reproduce the same triple-window with
slight regional variants. There is no single published logistic-
regression coefficient set for powdery mildew on Indian Alphonso, so
this module uses three independent Gaussian kernels (one per variable)
centered on the optimum of each band. The product of the three kernels
yields a smoothed [0, 1] risk that peaks inside the published window
and rolls off outside it.

Engineering estimate: kernel sigmas (default 2.5 degC, 4.0 degC, 7.0 %)
are picked so that risk drops to ~0.6 at the band edges and ~0.1 well
outside the band. Plan 4 Task 5 (calibration) can refit these against
real Konkan CROPSAP powdery-mildew outbreaks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# NHB / ICAR-CISH published bands. These are NOT engineering estimates --
# they're literature-pinned and the test suite guards against drift.
T_MIN_OPTIMAL_BAND: tuple[float, float] = (11.0, 14.0)
T_MAX_OPTIMAL_BAND: tuple[float, float] = (17.0, 31.0)
RH_OPTIMAL_BAND: tuple[float, float] = (64.0, 72.0)

# Engineering-estimate Gaussian sigmas; overridable via kwargs for calibration.
DEFAULT_SIGMAS: dict[str, float] = {
    "t_min": 2.5,
    "t_max": 4.0,
    "rh": 7.0,
}


@dataclass(frozen=True, slots=True)
class PowderyMildewInputs:
    t_max_c: float
    t_min_c: float
    rh_pct: float


def _band_kernel(value: float, band: tuple[float, float], sigma: float) -> float:
    """Gaussian distance from the nearest band edge, normalized to [0, 1].

    Inside the band: returns 1.0 (full risk).
    Outside the band: returns exp(-(distance / sigma)^2 / 2), so risk
    decays with the squared distance to the closest edge.
    """
    low, high = band
    if low <= value <= high:
        return 1.0
    distance = low - value if value < low else value - high
    return math.exp(-((distance / sigma) ** 2) / 2.0)


def powdery_mildew_risk(
    inp: PowderyMildewInputs,
    sigmas: dict[str, float] | None = None,
) -> float:
    """Probability-like powdery-mildew pressure score in [0, 1].

    Product of three Gaussian-band kernels on Tmin, Tmax, RH. Peaks at
    1.0 when ALL three variables are inside the published optimum
    window; smoothly decays outside.

    This is a pressure index, not a calibrated infection probability --
    the calibration notebook can sharpen the sigmas against real data,
    but the *shape* (peaks inside the documented band) is locked.
    """
    sigmas = sigmas if sigmas is not None else DEFAULT_SIGMAS
    k_tmin = _band_kernel(inp.t_min_c, T_MIN_OPTIMAL_BAND, sigmas["t_min"])
    k_tmax = _band_kernel(inp.t_max_c, T_MAX_OPTIMAL_BAND, sigmas["t_max"])
    k_rh = _band_kernel(inp.rh_pct, RH_OPTIMAL_BAND, sigmas["rh"])
    return k_tmin * k_tmax * k_rh
