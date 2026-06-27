"""Pesticide candidate ranker.

Per design spec section 4.3 Module 3c step 5, the ranker scores each
candidate active ingredient by::

    log_score = log(efficacy + EPSILON)
              - log(half_life + 1)
              - log(cost_per_acre + 1)

Higher score is better. The score combines three desiderata into one
scalar:

* **High efficacy** against the primary pathogen -> larger log
* **Short residue half-life** -> smaller subtraction -> larger score
  (matters for export markets where MRL compliance is tight)
* **Low cost per acre** -> smaller subtraction -> larger score
  (matters for the smallholder economics story)

Why log space? Half-life and cost both vary across one to two orders of
magnitude (sulphur 3 days vs chlorpyrifos 35 days; sulphur Rs.90 vs
flubendiamide Rs.620). Linear differences would let one term dominate;
log differences keep the three desiderata roughly comparable.

Ties are broken by lower half-life (faster residue clearance is preferred
when score is tied).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .pesticide_metadata import PesticideMetadata

_EFFICACY_EPSILON = 1.0e-6


@dataclass(frozen=True, slots=True)
class RankedCandidate:
    """A pesticide candidate with its computed ranker score."""

    metadata: PesticideMetadata
    pathogen: str
    log_score: float

    @property
    def active_ingredient(self) -> str:
        return self.metadata.active_ingredient


def _score(metadata: PesticideMetadata, pathogen: str) -> float:
    """Compute log_score per spec section 4.3.3c step 5."""
    efficacy = metadata.efficacy_against(pathogen)
    half_life = metadata.residue_half_life_days
    cost = metadata.cost_per_acre_inr
    return math.log(efficacy + _EFFICACY_EPSILON) - math.log(half_life + 1.0) - math.log(cost + 1.0)


def rank_candidates(
    candidates: list[PesticideMetadata],
    pathogen: str,
) -> list[RankedCandidate]:
    """Rank candidates against ``pathogen`` descending by log_score.

    Ties (within 1e-9 of each other) are broken by lower half-life.
    """
    scored: list[RankedCandidate] = [
        RankedCandidate(metadata=c, pathogen=pathogen, log_score=_score(c, pathogen))
        for c in candidates
    ]
    return sorted(
        scored,
        key=lambda r: (-r.log_score, r.metadata.residue_half_life_days),
    )


def top_n(
    candidates: list[PesticideMetadata],
    pathogen: str,
    n: int = 5,
) -> list[RankedCandidate]:
    """Convenience -- return the top ``n`` after ranking."""
    return rank_candidates(candidates, pathogen)[:n]
