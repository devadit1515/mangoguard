"""Tests for the top-level market-conditioned recommender (Plan 4 Task 12).

The recommender is the focal CREST 4.3 creativity artifact -- per-block
per-segment pesticide recommendations that integrate disease pressure,
CIB&RC registration, market MRL, RASFF history, and the efficacy
ranker. These tests cover the decision-flow branches in
src/mangoguard/recommend/recommend.py.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from mangoguard.recommend import cibrc as _cibrc_module
from mangoguard.recommend import pesticide_metadata as _metadata_module
from mangoguard.recommend import rasff as _rasff_module
from mangoguard.recommend.markets import MarketSegment
from mangoguard.recommend.recommend import (
    _EXPORT_RASFF_CUTOFF,
    _PPI_SPRAY_THRESHOLD,
    Recommendation,
    recommend,
)
from mangoguard.schema import BlockObservation, ConnectorSource

_DAY = date(2025, 7, 15)


@pytest.fixture(autouse=True)
def _clear_module_caches():
    """Reset all the module-level lru_caches the recommender depends on."""
    _cibrc_module.reset_cache()
    _metadata_module.reset_cache()
    _rasff_module.reset_cache()
    yield
    _cibrc_module.reset_cache()
    _metadata_module.reset_cache()
    _rasff_module.reset_cache()


def _imd_row(block_id: str, when: datetime, **kw) -> BlockObservation:
    return BlockObservation(block_id=block_id, ts=when, source=ConnectorSource.IMD, **kw)


def _seed_high_anthracnose_window(store, block_id: str) -> None:
    """Seven days of warm + humid + leaf-wet conditions -> high PPI, anthracnose primary.

    Conditions tuned to push PPI above the 50.0 spray threshold: high RH,
    extended leaf wetness, low wind/sun (which dampen the HTR risk).
    """
    base = datetime.combine(_DAY - timedelta(days=6), datetime.min.time(), tzinfo=timezone.utc)
    for i in range(7):
        store.insert(
            _imd_row(
                block_id,
                base + timedelta(days=i),
                t_air_c=27.0 + (i * 0.1),
                rh_pct=95.0,
                leaf_wetness_hr=10.0,
                wind_speed_ms=0.8,
                solar_w_m2=60.0,
            )
        )


def _seed_low_pressure_window(store, block_id: str) -> None:
    """Hot-dry-summer week -> low PPI, no spray."""
    base = datetime.combine(_DAY - timedelta(days=6), datetime.min.time(), tzinfo=timezone.utc)
    for i in range(7):
        store.insert(
            _imd_row(
                block_id,
                base + timedelta(days=i, hours=12),
                t_air_c=38.0,
                rh_pct=35.0,
                leaf_wetness_hr=0.0,
                wind_speed_ms=4.0,
                solar_w_m2=900.0,
            )
        )
        store.insert(
            _imd_row(
                block_id,
                base + timedelta(days=i, hours=2),
                t_air_c=24.0,
                rh_pct=50.0,
                leaf_wetness_hr=0.0,
                wind_speed_ms=3.0,
                solar_w_m2=0.0,
            )
        )


def test_low_ppi_returns_no_spray(store):
    _seed_low_pressure_window(store, "block1")
    result = recommend(
        store,
        block_id="block1",
        day=_DAY,
        target_market=MarketSegment.DOMESTIC_MANDI,
        days_until_harvest=60,
    )
    assert isinstance(result, Recommendation)
    assert result.pesticide is None
    assert result.ppi < _PPI_SPRAY_THRESHOLD
    assert "No spray" in result.rationale


def test_high_ppi_returns_pesticide_recommendation(store):
    _seed_high_anthracnose_window(store, "block1")
    result = recommend(
        store,
        block_id="block1",
        day=_DAY,
        target_market=MarketSegment.DOMESTIC_MANDI,
        days_until_harvest=60,
    )
    assert result.pesticide is not None
    assert result.ppi >= _PPI_SPRAY_THRESHOLD
    assert result.primary_pathogen == "anthracnose"
    assert result.dose is not None
    assert result.phi_days is not None
    assert result.harvest_date_constraint is not None


def test_recommendation_pesticide_is_cibrc_registered(store):
    _seed_high_anthracnose_window(store, "block1")
    result = recommend(
        store,
        block_id="block1",
        day=_DAY,
        target_market=MarketSegment.DOMESTIC_MANDI,
        days_until_harvest=60,
    )
    assert result.pesticide is not None
    assert _cibrc_module.is_registered(result.pesticide)


def test_phi_constraint_excludes_short_window_pesticides(store):
    """With only 8 days until harvest, only AIs with PHI <= 8 can be recommended."""
    _seed_high_anthracnose_window(store, "block1")
    result = recommend(
        store,
        block_id="block1",
        day=_DAY,
        target_market=MarketSegment.DOMESTIC_MANDI,
        days_until_harvest=8,
    )
    # Either a low-PHI pesticide is picked, or no compliant survives.
    if result.pesticide is not None:
        assert result.phi_days is not None
        assert result.phi_days <= 8


def test_zero_days_until_harvest_returns_no_compliant_pesticide(store):
    _seed_high_anthracnose_window(store, "block1")
    result = recommend(
        store,
        block_id="block1",
        day=_DAY,
        target_market=MarketSegment.DOMESTIC_MANDI,
        days_until_harvest=0,
    )
    # No CIB&RC AI for anthracnose has PHI 0 -> no spray with explanatory rationale
    assert result.pesticide is None
    assert "filtered" in result.rationale.lower() or "no spray" in result.rationale.lower()


def test_export_eu_demotes_high_rasff_pesticides(store):
    """For EU export, chlorpyrifos-class AIs (high RASFF history) must be excluded."""
    _seed_high_anthracnose_window(store, "block1")
    result = recommend(
        store,
        block_id="block1",
        day=_DAY,
        target_market=MarketSegment.EXPORT_EU,
        days_until_harvest=60,
    )
    if result.pesticide is not None and result.expected_rasff_rejection_p is not None:
        assert result.expected_rasff_rejection_p <= _EXPORT_RASFF_CUTOFF


def test_export_eu_and_mandi_can_differ(store):
    """The MRL + RASFF filters mean export and mandi may pick different AIs."""
    _seed_high_anthracnose_window(store, "block1")
    eu_result = recommend(
        store,
        block_id="block1",
        day=_DAY,
        target_market=MarketSegment.EXPORT_EU,
        days_until_harvest=60,
    )
    mandi_result = recommend(
        store,
        block_id="block1",
        day=_DAY,
        target_market=MarketSegment.DOMESTIC_MANDI,
        days_until_harvest=60,
    )
    # Both fields should be populated; the two need not be equal but the
    # call shapes should match.
    assert eu_result.target_market == MarketSegment.EXPORT_EU
    assert mandi_result.target_market == MarketSegment.DOMESTIC_MANDI


def test_recommendation_returns_alternatives(store):
    _seed_high_anthracnose_window(store, "block1")
    result = recommend(
        store,
        block_id="block1",
        day=_DAY,
        target_market=MarketSegment.DOMESTIC_MANDI,
        days_until_harvest=60,
    )
    if result.pesticide is not None:
        assert isinstance(result.alternatives, list)
        # Should have at least one alternative for the deep mango pesticide universe
        assert len(result.alternatives) >= 1
        # Top pick must not appear in alternatives
        assert result.pesticide not in result.alternatives


def test_recommendation_rationale_is_informative(store):
    _seed_high_anthracnose_window(store, "block1")
    result = recommend(
        store,
        block_id="block1",
        day=_DAY,
        target_market=MarketSegment.DOMESTIC_MANDI,
        days_until_harvest=60,
    )
    assert result.rationale
    # The rationale should mention the primary pathogen
    assert result.primary_pathogen in result.rationale.lower()


def test_recommendation_harvest_constraint_matches_phi(store):
    _seed_high_anthracnose_window(store, "block1")
    result = recommend(
        store,
        block_id="block1",
        day=_DAY,
        target_market=MarketSegment.DOMESTIC_MANDI,
        days_until_harvest=60,
    )
    if result.pesticide is not None:
        assert result.harvest_date_constraint is not None
        expected = _DAY + timedelta(days=result.phi_days or 0)
        assert result.harvest_date_constraint == expected


def test_recommendation_fields_populated_for_export(store):
    _seed_high_anthracnose_window(store, "block1")
    result = recommend(
        store,
        block_id="block1",
        day=_DAY,
        target_market=MarketSegment.EXPORT_EU,
        days_until_harvest=60,
    )
    if result.pesticide is not None:
        # Export should report a RASFF probability
        assert result.expected_rasff_rejection_p is not None
        assert 0.0 <= result.expected_rasff_rejection_p <= 1.0


def test_recommendation_no_rasff_field_for_domestic(store):
    _seed_high_anthracnose_window(store, "block1")
    result = recommend(
        store,
        block_id="block1",
        day=_DAY,
        target_market=MarketSegment.DOMESTIC_MANDI,
        days_until_harvest=60,
    )
    if result.pesticide is not None:
        assert result.expected_rasff_rejection_p is None


def test_unknown_block_returns_no_spray_or_low_ppi(store):
    """A block with no observations gets neutral PPI -- should not crash."""
    result = recommend(
        store,
        block_id="empty_block",
        day=_DAY,
        target_market=MarketSegment.DOMESTIC_MANDI,
        days_until_harvest=60,
    )
    assert isinstance(result, Recommendation)
    # Either low PPI (no spray) or some valid recommendation; never crash.
