"""Anthracnose infection-risk model (Akem 2006 humid-thermal-ratio logistic).

Reference
---------
Akem, C. N. (2006). "Mango anthracnose disease: present status and future
research priorities." *Plant Pathology Journal* 5(3): 266-273. Akem fits a
logistic regression of post-flowering anthracnose infection events against
four field-measurable weather variables, reporting R^2 = 0.93 across
multi-season observations.

The model
---------
The humid-thermal ratio (HTR) proxies the microclimate window in which
*Colletotrichum gloeosporioides* conidia germinate and penetrate the fruit
cuticle::

    HTR = morning relative humidity (%) / daily temperature range (Tmax - Tmin)

A muggy, overcast day (high RH, small day-night swing) keeps the leaf surface
wet longer and pushes HTR up; a dry day with a big swing pushes it down. Long
leaf wetness extends germination; sunshine and wind dry the surface and
scatter inoculum. The infection probability is a logistic of a linear score::

    z = b0 + b_htr*HTR + b_lw*leaf_wetness_hr + b_sun*sunshine_hr + b_wind*wind_ms
    P(infection in next 24 h) = sigma(z) = 1 / (1 + exp(-z))

Why logistic? Infection is a yes/no event, so the response must be a
probability in [0, 1]; a plain linear fit can leave that range. The sigmoid
maps any real z onto (0, 1), and each coefficient has a clean reading: a unit
rise in a variable multiplies the odds P/(1-P) by exp(b). The signs encode the
biology: b_htr, b_lw > 0 (humidity and wetness promote infection);
b_sun, b_wind < 0 (sun and wind suppress it).

The default coefficients are reproduced from the Akem paper. They are baselines
a deployment would refit on local records; the value is passed as ``coeffs=``.
This module is variety-agnostic: cultivar susceptibility is applied downstream
in ``ppi.py``, because it shifts the *level* of risk, not the weather response.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Akem (2006) coefficients. Baselines; a deployment refits these on local data.
DEFAULT_COEFFS: dict[str, float] = {
    "beta_0": -4.2,
    "beta_htr": 0.085,
    "beta_lw": 0.32,
    "beta_sun": -0.18,
    "beta_wind": -0.12,
}

# Below this diurnal range the HTR denominator is clamped (saturated-microclimate
# limit, e.g. a heavy-overcast monsoon day with Tmax == Tmin). Same clamp Akem
# used in his own data reduction; prevents division-by-zero.
MIN_DIURNAL_RANGE_C = 0.1


@dataclass(frozen=True, slots=True)
class AnthracnoseInputs:
    """Field-measurable inputs for one day at one block.

    The caller handles unit conversions (e.g. sensor leaf-wetness minutes ->
    hours) before constructing this record.
    """

    t_max_c: float
    t_min_c: float
    rh_morning_pct: float
    leaf_wetness_hr: float
    sunshine_hr: float
    wind_speed_ms: float


def humid_thermal_ratio(t_max_c: float, t_min_c: float, rh_morning_pct: float) -> float:
    """HTR = morning RH / daily temperature range, with the saturated clamp."""
    return rh_morning_pct / max(MIN_DIURNAL_RANGE_C, t_max_c - t_min_c)


def anthracnose_risk(
    inp: AnthracnoseInputs,
    coeffs: dict[str, float] | None = None,
) -> float:
    """Probability of an anthracnose infection event in the next 24 hours.

    Pure function returning a value in [0, 1]: no I/O, no global state,
    deterministic for given inputs. Uses the numerically stable form of the
    logistic (``exp(z)/(1+exp(z))`` for negative z) to avoid overflow.
    """
    coeffs = coeffs if coeffs is not None else DEFAULT_COEFFS
    htr = humid_thermal_ratio(inp.t_max_c, inp.t_min_c, inp.rh_morning_pct)
    z = (
        coeffs["beta_0"]
        + coeffs["beta_htr"] * htr
        + coeffs["beta_lw"] * inp.leaf_wetness_hr
        + coeffs["beta_sun"] * inp.sunshine_hr
        + coeffs["beta_wind"] * inp.wind_speed_ms
    )
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    ez = math.exp(z)
    return ez / (1.0 + ez)
