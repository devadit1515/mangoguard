"""Infection-risk index, cultivar susceptibility, and the spray-decision rules.

The node turns the Akem probability into a 0-100 risk percentage, shifted by a
per-variety susceptibility so the same weather reads as more dangerous on a
highly susceptible cultivar (Alphonso) than a tolerant one. Two spray rules are
provided for the spray-reduction study: the status-quo fixed *calendar*, and the
*early-warning* rule the node enables (spray only when risk is sustained, with a
protection lockout afterwards).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from aamrakshak.riskengine.anthracnose import (
    DEFAULT_COEFFS,
    AnthracnoseInputs,
    anthracnose_risk,
)

# Relative odds multipliers for cultivar susceptibility to anthracnose.
# Illustrative ordering from horticultural literature (Alphonso is notably
# susceptible); these scale the *level* of risk, not the weather response, and
# are applied without retraining the model -- the basis of success condition S5.
VARIETY_SUSCEPTIBILITY: dict[str, float] = {
    "alphonso": 1.00,
    "langra": 0.85,
    "dasheri": 0.80,
    "banganapalli": 0.75,
    "kesar": 0.70,
    "totapuri": 0.60,
}


def infection_risk_pct(
    inp: AnthracnoseInputs,
    variety: str = "alphonso",
    coeffs: dict[str, float] | None = None,
) -> float:
    """Anthracnose infection risk as a 0-100 percentage for a cultivar.

    Cultivar susceptibility is applied as an odds multiplier:
    ``odds' = s * odds``, which is the correct way to shift a logistic level
    while leaving the weather sensitivity intact.
    """
    coeffs = coeffs if coeffs is not None else DEFAULT_COEFFS
    p = anthracnose_risk(inp, coeffs)
    s = VARIETY_SUSCEPTIBILITY.get(variety.lower(), 1.0)
    if s != 1.0:
        odds = p / max(1e-9, 1.0 - p)
        odds *= s
        p = odds / (1.0 + odds)
    return 100.0 * p


@dataclass(frozen=True, slots=True)
class SprayEvent:
    """One fungicide application: which day, and why it was triggered."""

    day: int
    reason: str


def spray_schedule_calendar(
    n_days: int,
    interval_days: int = 12,
    first_spray_day: int = 5,
) -> list[SprayEvent]:
    """Status-quo fixed-calendar spraying, every ``interval_days`` regardless of
    weather. Default ~12-day interval approximates the ICAR-CISH flowering-to-
    harvest schedule. This is the baseline the node is trying to beat.
    """
    days = range(first_spray_day, n_days, interval_days)
    return [SprayEvent(day=d, reason="calendar") for d in days]


def spray_schedule_early_warning(
    risk_pct: Sequence[float],
    threshold: float = 50.0,
    sustain_days: int = 2,
    lockout_days: int = 10,
) -> list[SprayEvent]:
    """Spray only when risk is *sustained* above threshold, then hold off.

    A single spike does not trigger a spray (sustain window suppresses noise);
    after spraying, a ``lockout_days`` window models the residual protection of
    a contact fungicide, so the rule cannot over-fire. This conservative shape
    is what lets the node cut sprays without missing genuine infection windows.
    """
    events: list[SprayEvent] = []
    protected_until = -1
    run = 0
    for day, r in enumerate(risk_pct):
        run = run + 1 if r >= threshold else 0
        if run >= sustain_days and day > protected_until:
            events.append(SprayEvent(day=day, reason=f"risk>={threshold:.0f}% for {sustain_days}d"))
            protected_until = day + lockout_days
    return events
