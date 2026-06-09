"""Top-level market-conditioned recommender (Plan 4 Task 12, FOCAL).

This module is the focal research artifact of MangoGuard (CREST 4.3
creativity anchor): given a block, a date, a target market, and a
days-until-harvest window, it produces a per-block per-segment
recommendation that integrates

* the disease-pressure index (PPI, ``risk.ppi``)
* the CIB&RC registered-pesticide list (``recommend.cibrc``)
* the target market's MRL chain (``recommend.markets`` + ``mrl_loader``)
* RASFF historical rejection probability for export segments
  (``recommend.rasff``)
* the efficacy/half-life/cost ranker (``recommend.ranker``)

Decision flow per spec section 4.3 Module 3c:

1. ``compute_ppi`` -- if PPI < ``_PPI_SPRAY_THRESHOLD``, return a no-spray
   recommendation. Saves money, residue, and farmer time.
2. Identify the **primary pathogen** (component with the highest score).
3. Pull all CIB&RC-registered active ingredients for that pathogen.
4. Filter by PHI: exclude any AI whose conservative (max) PHI exceeds
   the days-until-harvest window. (Spraying with insufficient PHI risks
   residue violations at harvest.)
5. Filter by MRL: exclude any AI whose target-market MRL strictest
   value is at-or-below the destination's default floor when the AI has
   no listed MRL. (Conservative -- if the destination doesn't list it,
   we don't recommend it.)
6. For export segments (EU/Gulf) apply the **RASFF filter**: exclude
   any AI whose smoothed historical rejection probability against that
   destination exceeds ``_EXPORT_RASFF_CUTOFF``.
7. Rank the survivors by ``ranker.rank_candidates``.
8. Return the top survivor plus up to ``_N_ALTERNATIVES`` runners-up.

If every step empties the candidate pool, return a no-spray
recommendation with an explanatory rationale.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from mangoguard.risk.ppi import compute_ppi, primary_pathogen
from mangoguard.store import FeedStore

from . import cibrc, mrl_loader, rasff
from .markets import MarketSegment, mrl_tables_for
from .pesticide_metadata import PesticideMetadata, all_metadata, lookup
from .ranker import RankedCandidate, rank_candidates

# Decision-flow thresholds (kept module-level so they're discoverable
# from tests / notebooks).
_PPI_SPRAY_THRESHOLD = 50.0
_EXPORT_RASFF_CUTOFF = 0.20
_N_ALTERNATIVES = 3
_EXPORT_SEGMENTS = frozenset({MarketSegment.EXPORT_EU, MarketSegment.EXPORT_GULF})

# Maps MarketSegment -> RASFF destination key (uppercase) used in
# ``rasff_mango_rejections.csv``. Domestic segments are not RASFF-filtered.
_RASFF_DESTINATION = {
    MarketSegment.EXPORT_EU: "EU",
    MarketSegment.EXPORT_GULF: "GULF",
}


@dataclass(frozen=True, slots=True)
class Recommendation:
    """Outcome of a single ``recommend()`` call.

    Fields are populated according to the decision flow. ``pesticide`` is
    ``None`` when no spray is recommended (either PPI below threshold or
    no compliant pesticide survives the filters).
    """

    block_id: str
    date: date
    ppi: float
    primary_pathogen: str
    target_market: MarketSegment
    pesticide: str | None
    dose: str | None
    phi_days: int | None
    harvest_date_constraint: date | None
    expected_rasff_rejection_p: float | None
    alternatives: list[str] = field(default_factory=list)
    rationale: str = ""


def _no_spray(
    block_id: str,
    day: date,
    ppi: float,
    pathogen: str,
    market: MarketSegment,
    rationale: str,
) -> Recommendation:
    return Recommendation(
        block_id=block_id,
        date=day,
        ppi=ppi,
        primary_pathogen=pathogen,
        target_market=market,
        pesticide=None,
        dose=None,
        phi_days=None,
        harvest_date_constraint=None,
        expected_rasff_rejection_p=None,
        rationale=rationale,
    )


def _phi_compliant(
    ai: str,
    days_until_harvest: int,
) -> bool:
    """An AI is PHI-compliant when its conservative (max) PHI fits the harvest window."""
    phi = cibrc.max_phi_days(ai)
    return phi is not None and phi <= days_until_harvest


def _mrl_compliant(
    ai: str,
    market: MarketSegment,
) -> bool:
    """An AI is MRL-compliant when the strictest MRL across the target market's
    chain is *defined* (i.e., the destination has a listing for the AI).

    Unlisted = unknown risk -> excluded for export markets; allowed for
    domestic markets where the default FSSAI floor governs.
    """
    market_chain = mrl_tables_for(market)
    strictest = mrl_loader.strictest_mrl(market_chain, ai)
    if strictest is not None:
        return True
    # No listing. Domestic markets fall back to default_floor; for export
    # markets we'd rather exclude than recommend an un-listed AI.
    return market not in _EXPORT_SEGMENTS


def _rasff_compliant(
    ai: str,
    market: MarketSegment,
) -> tuple[bool, float | None]:
    """For export segments, exclude AIs whose smoothed rejection probability
    exceeds the cutoff. Returns ``(compliant, p_hat_or_None)``.
    """
    if market not in _EXPORT_SEGMENTS:
        return True, None
    destination = _RASFF_DESTINATION[market]
    p_hat = rasff.rejection_probability(ai, destination)
    return p_hat <= _EXPORT_RASFF_CUTOFF, p_hat


def _pick_dose(ai: str) -> str | None:
    """First CIB&RC dose listed for the AI (multiple registrations may share an AI)."""
    for entry in cibrc.all_entries():
        if entry.active_ingredient == ai:
            return entry.dose_per_liter_water
    return None


def recommend(
    store: FeedStore,
    block_id: str,
    day: date,
    target_market: MarketSegment,
    days_until_harvest: int,
) -> Recommendation:
    """Per spec section 4.3 Module 3c decision flow.

    Args:
        store: Feed store backing ``compute_ppi``.
        block_id: Orchard block identifier.
        day: Decision day.
        target_market: Where the fruit is destined (EU export / Gulf
            export / domestic retail / domestic mandi).
        days_until_harvest: Days between ``day`` and planned harvest.

    Returns:
        A ``Recommendation`` with the top pesticide (or no-spray) plus
        rationale and alternatives.
    """
    components = compute_ppi(store, block_id, day)
    ppi = float(components["ppi"])
    pathogen = primary_pathogen(components)

    if ppi < _PPI_SPRAY_THRESHOLD:
        return _no_spray(
            block_id,
            day,
            ppi,
            pathogen,
            target_market,
            rationale=(
                f"No spray: PPI {ppi:.1f} is below the {_PPI_SPRAY_THRESHOLD:.0f} "
                "spray threshold. Monitor and reassess in 3-5 days."
            ),
        )

    # Step 3: CIB&RC-registered AIs for the primary pathogen.
    cibrc_rows = cibrc.pesticides_for_pathogen(pathogen)
    if not cibrc_rows:
        return _no_spray(
            block_id,
            day,
            ppi,
            pathogen,
            target_market,
            rationale=(
                f"No spray: no CIB&RC-registered active ingredient targets "
                f"'{pathogen}'. Manual decision required -- consult ICAR-CISH "
                "or KVK extension officer."
            ),
        )
    registered_ais = {row.active_ingredient for row in cibrc_rows}

    # Steps 4 + 5 + 6: apply PHI, MRL, RASFF filters.
    survivors_meta: list[PesticideMetadata] = []
    rasff_probs: dict[str, float] = {}
    filter_audit = {"phi": 0, "mrl": 0, "rasff": 0}
    for ai in sorted(registered_ais):
        if not _phi_compliant(ai, days_until_harvest):
            filter_audit["phi"] += 1
            continue
        if not _mrl_compliant(ai, target_market):
            filter_audit["mrl"] += 1
            continue
        rasff_ok, p_hat = _rasff_compliant(ai, target_market)
        if not rasff_ok:
            filter_audit["rasff"] += 1
            continue
        meta = lookup(ai)
        if meta is None:
            # No metadata -> can't rank; skip with a quieter audit.
            continue
        survivors_meta.append(meta)
        if p_hat is not None:
            rasff_probs[ai] = p_hat

    if not survivors_meta:
        return _no_spray(
            block_id,
            day,
            ppi,
            pathogen,
            target_market,
            rationale=(
                f"No spray: {len(registered_ais)} CIB&RC-registered "
                f"{pathogen}-active ingredients were filtered "
                f"({filter_audit['phi']} by PHI > {days_until_harvest}d, "
                f"{filter_audit['mrl']} by MRL non-listing for "
                f"{target_market.value}, "
                f"{filter_audit['rasff']} by RASFF >{_EXPORT_RASFF_CUTOFF:.2f}). "
                "Delay harvest, switch market segment, or seek extension advice."
            ),
        )

    # Step 7 + 8: rank + slice.
    ranked: list[RankedCandidate] = rank_candidates(survivors_meta, pathogen)
    top = ranked[0]
    alternatives = [r.active_ingredient for r in ranked[1 : 1 + _N_ALTERNATIVES]]
    top_phi = cibrc.max_phi_days(top.active_ingredient) or 0
    harvest_constraint = day + timedelta(days=top_phi)

    rationale = (
        f"Spray {top.active_ingredient} for {pathogen} (PPI {ppi:.1f}). "
        f"CIB&RC-registered, "
        f"MRL-compliant for {target_market.value}, "
        f"PHI {top_phi}d <= {days_until_harvest}d harvest window."
    )
    if target_market in _EXPORT_SEGMENTS and top.active_ingredient in rasff_probs:
        rationale += (
            f" RASFF rejection probability "
            f"{rasff_probs[top.active_ingredient]:.3f} <= "
            f"{_EXPORT_RASFF_CUTOFF:.2f} export cutoff."
        )

    return Recommendation(
        block_id=block_id,
        date=day,
        ppi=ppi,
        primary_pathogen=pathogen,
        target_market=target_market,
        pesticide=top.active_ingredient,
        dose=_pick_dose(top.active_ingredient),
        phi_days=top_phi,
        harvest_date_constraint=harvest_constraint,
        expected_rasff_rejection_p=rasff_probs.get(top.active_ingredient),
        alternatives=alternatives,
        rationale=rationale,
    )


# Convenience re-exports for the integration test + notebooks.
__all__ = [
    "Recommendation",
    "recommend",
    "_PPI_SPRAY_THRESHOLD",
    "_EXPORT_RASFF_CUTOFF",
    "all_metadata",
]
