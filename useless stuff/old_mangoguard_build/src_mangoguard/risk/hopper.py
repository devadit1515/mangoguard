"""Mango hopper infection-risk model.

Mango hopper (*Idioscopus clypealis*, *Amritodus atkinsoni*, *Idioscopus
niveosparsus*) is the dominant insect pest on Konkan Alphonso during
flowering. CROPSAP's Maharashtra taluka surveillance reports adult
hopper population density per panicle as a percent-infestation figure.

Model
-----
Hopper risk at a block is the product of two factors:

1. **CROPSAP regional pressure** -- the taluka-level infestation
   percent the connector wrote into ``cropsap_pest_pressure``. Higher
   regional pressure means more inoculum / migratory adult population
   in the surrounding orchards.
2. **Local temperature multiplier** -- a triangular kernel that peaks
   at T == 27 degC and drops linearly to zero at the published thermal
   limits (T <= 18 degC or T >= 36 degC). Below 18 degC hopper activity
   stalls; above 36 degC desiccation suppresses populations. The 27 degC
   optimum is reproduced from ICAR-CISH forewarning bulletins.

::

    hopper_risk = (cropsap_pct / 100) * t_multiplier(T)

The CROPSAP pressure is normalized from percent to [0, 1] inside the
model so callers can pass the raw connector value.
"""

from __future__ import annotations

# ICAR-CISH thermal optimum band for mango hopper. Locked constants,
# guarded by the test suite.
T_OPTIMUM_C: float = 27.0
T_LOWER_LIMIT_C: float = 18.0
T_UPPER_LIMIT_C: float = 36.0


def _temperature_multiplier(t_air_c: float) -> float:
    """Triangular kernel: peaks at 27 degC, zero outside [18, 36] degC."""
    if t_air_c <= T_LOWER_LIMIT_C or t_air_c >= T_UPPER_LIMIT_C:
        return 0.0
    if t_air_c <= T_OPTIMUM_C:
        return (t_air_c - T_LOWER_LIMIT_C) / (T_OPTIMUM_C - T_LOWER_LIMIT_C)
    return (T_UPPER_LIMIT_C - t_air_c) / (T_UPPER_LIMIT_C - T_OPTIMUM_C)


def hopper_risk(cropsap_taluka_pressure: float, t_air_c: float) -> float:
    """Mango-hopper infection-risk score in [0, 1].

    Parameters
    ----------
    cropsap_taluka_pressure
        Percent infestation reported by the CROPSAP connector for the
        block's taluka. Values outside [0, 100] are clamped.
    t_air_c
        Local block temperature in degC.
    """
    pressure_norm = max(0.0, min(100.0, cropsap_taluka_pressure)) / 100.0
    t_mult = _temperature_multiplier(t_air_c)
    return pressure_norm * t_mult
