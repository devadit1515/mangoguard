"""Market segments and their associated MRL-table lookup chain.

A Konkan Alphonso block can target one of four market segments per
harvest, each with a different MRL constraint chain:

- ``EXPORT_EU`` -- EU + Japan strict MRLs (often 0.01 mg/kg detection-
  limit floors). ~1-2% of Indian mango exports.
- ``EXPORT_GULF`` -- Codex Alimentarius MRLs, less strict than EU.
  ~2-3% of exports (Gulf, Middle East, SE Asia).
- ``DOMESTIC_RETAIL`` -- FSSAI floor + buyer-specific stricter limits
  (Reliance, DMart, Maaza, Frooti). ~25-30% of domestic volume.
- ``DOMESTIC_MANDI`` -- FSSAI MRL floor only. ~60-65% of domestic
  volume (traditional wholesale).

Each segment maps to an ordered chain of MRL tables; the recommender
applies them as ``min(all_applicable_limits)``. Buyer-specific tables
exist as a stub for Plan 6 dashboard work; for now they fall back to
FSSAI.
"""

from __future__ import annotations

from enum import Enum


class MarketSegment(str, Enum):
    """Four target markets a Konkan Alphonso harvest can be routed to."""

    EXPORT_EU = "export_eu_japan_us"
    EXPORT_GULF = "export_gulf_me_seasia"
    DOMESTIC_RETAIL = "domestic_retail_processor"
    DOMESTIC_MANDI = "domestic_mandi"


# Ordered MRL-table lookup chain per segment. The recommender picks the
# strictest applicable limit (min across the chain) for any given active
# ingredient. Names refer to YAML files in ``data/mrl_tables/``.
MARKET_MRL_TABLE: dict[MarketSegment, list[str]] = {
    MarketSegment.EXPORT_EU: ["eu", "japan"],
    MarketSegment.EXPORT_GULF: ["codex"],
    MarketSegment.DOMESTIC_RETAIL: ["fssai", "buyer_specific"],
    MarketSegment.DOMESTIC_MANDI: ["fssai"],
}


def mrl_tables_for(segment: MarketSegment) -> list[str]:
    """Return the ordered MRL-table chain for a given market segment.

    Raises ``KeyError`` if the segment has no chain registered (defensive
    guard against future enum additions).
    """
    if segment not in MARKET_MRL_TABLE:
        msg = f"no MRL-table chain registered for {segment!r}"
        raise KeyError(msg)
    return list(MARKET_MRL_TABLE[segment])
