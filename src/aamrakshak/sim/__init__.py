"""Physically-grounded, seeded simulation of mango weather and outbreaks.

Everything here is clearly *simulated* (the report says so). The weather
generator is anchored on documented Konkan and Gujarat climate normals; the
outbreak-label generator is deliberately a DIFFERENT functional form from the
Akem risk model under test, so the backtest cannot be circular. One fixed seed
generates the ground truth once; only sensor noise varies between tiers.
"""

from aamrakshak.sim.outbreaks import OUTBREAK_COEFFS, add_outbreak_labels
from aamrakshak.sim.sensors import (
    TIER_LABELS,
    tier_risk_scores,
)
from aamrakshak.sim.weather import REGIONS, RegionProfile, generate_panel

__all__ = [
    "OUTBREAK_COEFFS",
    "REGIONS",
    "TIER_LABELS",
    "RegionProfile",
    "add_outbreak_labels",
    "generate_panel",
    "tier_risk_scores",
]
