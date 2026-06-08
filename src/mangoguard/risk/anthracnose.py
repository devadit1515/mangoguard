"""Anthracnose infection-risk model (Akem 2006 HTR logistic regression).

Reference
---------
Akem, C. N. (2006). "Mango anthracnose disease: present status and future
research priorities." Plant Pathology Journal 5(3): 266-273. Akem reports
a logistic regression of post-flowering anthracnose infection events
against four field-measurable variables, with R^2 = 0.93 across multi-
season observations.

The model
---------
HTR = humid-thermal ratio = (morning RH) / (daily T-range), proxying the
microclimate window in which *Colletotrichum gloeosporioides* conidia
germinate and penetrate the cuticle. Long leaf wetness extends spore
germination; sunshine and wind reduce inoculum survival/dispersal.

::

    logit(P) = beta_0
             + beta_htr  * HTR
             + beta_lw   * leaf_wetness_hours
             + beta_sun  * sunshine_hours
             + beta_wind * wind_speed_ms
    P_infection = 1 / (1 + exp(-logit(P)))

The default coefficients are reproduced from the Akem paper. Plan 4
Task 5 (``calibration.py``) refits these against the cooperating
farmer's 2018-2024 retrospective record + CROPSAP outbreak labels for
the Konkan Alphonso microclimate; the fitted coefficients are dumped
to ``artifacts/anthracnose_coeffs.yaml`` and can be passed as the
``coeffs=`` kwarg.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Akem (2006) Konkan-applicable coefficients. These are baselines --
# Plan 4 Task 17 (notebook 02) recalibrates them on Indian Alphonso data.
DEFAULT_COEFFS: dict[str, float] = {
    "beta_0": -4.2,
    "beta_htr": 0.085,
    "beta_lw": 0.32,
    "beta_sun": -0.18,
    "beta_wind": -0.12,
}


@dataclass(frozen=True, slots=True)
class AnthracnoseInputs:
    """Field-measurable inputs for one day at one block.

    All fields are required; the caller is responsible for any unit
    conversions (e.g., Pessl leaf-wetness minutes -> hours) before
    constructing this dataclass.
    """

    t_max_c: float
    t_min_c: float
    rh_morning_pct: float
    leaf_wetness_hr: float
    sunshine_hr: float
    wind_speed_ms: float


def anthracnose_risk(
    inp: AnthracnoseInputs,
    coeffs: dict[str, float] | None = None,
) -> float:
    """Probability of an anthracnose infection event in the next 24 hours.

    Returns a value in [0, 1]. Pure function: no I/O, no global state,
    deterministic for given inputs.

    Edge cases
    ----------
    - Tmax == Tmin (no diurnal range, e.g., heavy-overcast monsoon day):
      HTR denominator clamped to ``0.1`` to avoid division-by-zero. This
      represents the "saturated microclimate" limit and is the same
      clamp Akem used in his data reductions.
    - Negative leaf wetness, negative sunshine etc. are not validated
      here -- they'd be unphysical, but the caller (e.g., compute_ppi)
      should sanitize. The logistic squashes any finite z to [0, 1].
    """
    coeffs = coeffs if coeffs is not None else DEFAULT_COEFFS
    htr = inp.rh_morning_pct / max(0.1, inp.t_max_c - inp.t_min_c)
    z = (
        coeffs["beta_0"]
        + coeffs["beta_htr"] * htr
        + coeffs["beta_lw"] * inp.leaf_wetness_hr
        + coeffs["beta_sun"] * inp.sunshine_hr
        + coeffs["beta_wind"] * inp.wind_speed_ms
    )
    # Numerically stable logistic: avoid overflow for very negative z.
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    ez = math.exp(z)
    return ez / (1.0 + ez)
