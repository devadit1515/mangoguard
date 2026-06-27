"""Full Module 3 integration test (Plan 4 Task 16).

Verifies the complete spray-audit-and-recommender stack runs end-to-end
against a synthetic FeedStore:

  1. Insert 30 days of IMD weather observations.
  2. Insert 4 Sentinel-2 NDRE samples (block-level canopy stress).
  3. Insert 1 CROPSAP outbreak record (taluka hopper pressure).
  4. Run compute_ppi -- assert PPI is high (>=50) on the outbreak day.
  5. Run recommend() for all 4 MarketSegment values:
      - EU export, Gulf export, domestic retail, domestic mandi.
  6. Assert each non-None recommendation is
      a) CIB&RC-registered for the primary pathogen
      b) PHI-compliant given a 60-day harvest window
      c) MRL-compliant for that segment's chain
      d) (For exports) RASFF rejection probability under the cutoff
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from mangoguard.recommend import cibrc, mrl_loader
from mangoguard.recommend import pesticide_metadata as _metadata_module
from mangoguard.recommend import rasff as _rasff_module
from mangoguard.recommend.markets import MarketSegment, mrl_tables_for
from mangoguard.recommend.recommend import (
    _EXPORT_RASFF_CUTOFF,
    _PPI_SPRAY_THRESHOLD,
    recommend,
)
from mangoguard.risk.ppi import compute_ppi
from mangoguard.schema import BlockObservation, ConnectorSource

_DAY = date(2025, 7, 15)
_BLOCK_ID = "ratnagiri_block_A"
_TALUKA_HOPPER_KEY = "ratnagiri_hopper"
_HARVEST_DAYS = 60


@pytest.fixture(autouse=True)
def _clear_module_caches():
    cibrc.reset_cache()
    mrl_loader.reset_cache()
    _metadata_module.reset_cache()
    _rasff_module.reset_cache()
    yield
    cibrc.reset_cache()
    mrl_loader.reset_cache()
    _metadata_module.reset_cache()
    _rasff_module.reset_cache()


def _imd_row(block_id: str, when: datetime, **kw) -> BlockObservation:
    return BlockObservation(block_id=block_id, ts=when, source=ConnectorSource.IMD, **kw)


def _seed_disease_pressure(store, block_id: str) -> None:
    """30 days of warm + humid + leaf-wet conditions -> high anthracnose pressure."""
    base = datetime.combine(_DAY - timedelta(days=29), datetime.min.time(), tzinfo=timezone.utc)
    for i in range(30):
        store.insert(
            _imd_row(
                block_id,
                base + timedelta(days=i),
                t_air_c=27.0 + (i * 0.05),
                rh_pct=94.0,
                leaf_wetness_hr=9.0,
                wind_speed_ms=1.0,
                solar_w_m2=80.0,
            )
        )


def _seed_ndre_samples(store, block_id: str) -> None:
    """Four Sentinel-2 NDRE samples in the past 30 days, last one showing stress."""
    base = datetime.combine(_DAY - timedelta(days=28), datetime.min.time(), tzinfo=timezone.utc)
    ndre_values = [0.55, 0.52, 0.48, 0.42]  # declining = canopy stress
    for i, ndre in enumerate(ndre_values):
        store.insert(
            BlockObservation(
                block_id=block_id,
                ts=base + timedelta(days=i * 7),
                source=ConnectorSource.SENTINEL2,
                ndre=ndre,
            )
        )


def _seed_cropsap_outbreak(store, taluka_key: str) -> None:
    """One CROPSAP hopper outbreak record for the taluka pressure layer."""
    store.insert(
        BlockObservation(
            block_id=taluka_key,
            ts=datetime.combine(_DAY, datetime.min.time(), tzinfo=timezone.utc),
            source=ConnectorSource.CROPSAP,
            cropsap_pest_pressure=45.0,  # moderate hopper pressure
        )
    )


def test_full_module3_integration_high_ppi(store):
    """The high-pressure window must produce PPI >= spray threshold."""
    _seed_disease_pressure(store, _BLOCK_ID)
    _seed_ndre_samples(store, _BLOCK_ID)
    _seed_cropsap_outbreak(store, _TALUKA_HOPPER_KEY)

    components = compute_ppi(store, _BLOCK_ID, _DAY)
    assert (
        components["ppi"] >= _PPI_SPRAY_THRESHOLD
    ), f"expected PPI >= {_PPI_SPRAY_THRESHOLD}, got {components['ppi']:.1f}"


@pytest.mark.parametrize(
    "segment",
    [
        MarketSegment.EXPORT_EU,
        MarketSegment.EXPORT_GULF,
        MarketSegment.DOMESTIC_RETAIL,
        MarketSegment.DOMESTIC_MANDI,
    ],
)
def test_full_module3_integration_per_segment(store, segment):
    """recommend() must run without crashing for every market segment."""
    _seed_disease_pressure(store, _BLOCK_ID)
    _seed_ndre_samples(store, _BLOCK_ID)
    _seed_cropsap_outbreak(store, _TALUKA_HOPPER_KEY)

    result = recommend(
        store,
        block_id=_BLOCK_ID,
        day=_DAY,
        target_market=segment,
        days_until_harvest=_HARVEST_DAYS,
    )
    assert result.block_id == _BLOCK_ID
    assert result.target_market == segment
    assert result.ppi >= 0.0
    assert result.rationale


def test_recommended_pesticide_is_cibrc_registered_for_primary_pathogen(store):
    """The picked AI must be registered in CIB&RC for the primary pathogen."""
    _seed_disease_pressure(store, _BLOCK_ID)
    _seed_ndre_samples(store, _BLOCK_ID)
    _seed_cropsap_outbreak(store, _TALUKA_HOPPER_KEY)

    result = recommend(
        store,
        block_id=_BLOCK_ID,
        day=_DAY,
        target_market=MarketSegment.DOMESTIC_MANDI,
        days_until_harvest=_HARVEST_DAYS,
    )
    if result.pesticide is not None:
        registered_for_pathogen = {
            e.active_ingredient for e in cibrc.pesticides_for_pathogen(result.primary_pathogen)
        }
        assert result.pesticide in registered_for_pathogen


def test_recommended_pesticide_passes_mrl_filter(store):
    """For domestic mandi (FSSAI fallback) the picked AI may not be listed,
    but for EU/Japan export it MUST appear in the destination's chain."""
    _seed_disease_pressure(store, _BLOCK_ID)
    _seed_ndre_samples(store, _BLOCK_ID)
    _seed_cropsap_outbreak(store, _TALUKA_HOPPER_KEY)

    for segment in (MarketSegment.EXPORT_EU, MarketSegment.EXPORT_GULF):
        result = recommend(
            store,
            block_id=_BLOCK_ID,
            day=_DAY,
            target_market=segment,
            days_until_harvest=_HARVEST_DAYS,
        )
        if result.pesticide is not None:
            chain = mrl_tables_for(segment)
            strictest = mrl_loader.strictest_mrl(chain, result.pesticide)
            # Either there's a defined MRL (export should always have one)
            # or the picked AI was filtered as MRL-unlisted.
            assert strictest is not None, (
                f"{segment} picked {result.pesticide} but it's not in any "
                f"MRL table of the chain {chain}"
            )


def test_recommended_pesticide_phi_fits_harvest_window(store):
    _seed_disease_pressure(store, _BLOCK_ID)
    _seed_ndre_samples(store, _BLOCK_ID)
    _seed_cropsap_outbreak(store, _TALUKA_HOPPER_KEY)

    result = recommend(
        store,
        block_id=_BLOCK_ID,
        day=_DAY,
        target_market=MarketSegment.DOMESTIC_MANDI,
        days_until_harvest=_HARVEST_DAYS,
    )
    if result.pesticide is not None:
        assert result.phi_days is not None
        assert result.phi_days <= _HARVEST_DAYS


def test_export_recommendation_rasff_below_cutoff(store):
    _seed_disease_pressure(store, _BLOCK_ID)
    _seed_ndre_samples(store, _BLOCK_ID)
    _seed_cropsap_outbreak(store, _TALUKA_HOPPER_KEY)

    result = recommend(
        store,
        block_id=_BLOCK_ID,
        day=_DAY,
        target_market=MarketSegment.EXPORT_EU,
        days_until_harvest=_HARVEST_DAYS,
    )
    if result.pesticide is not None and result.expected_rasff_rejection_p is not None:
        assert result.expected_rasff_rejection_p <= _EXPORT_RASFF_CUTOFF


def test_eu_and_mandi_may_pick_different_ais(store):
    """Demonstrates the segment-conditioning effect: same orchard, same day,
    different market => potentially different pesticide recommendation."""
    _seed_disease_pressure(store, _BLOCK_ID)
    _seed_ndre_samples(store, _BLOCK_ID)
    _seed_cropsap_outbreak(store, _TALUKA_HOPPER_KEY)

    eu = recommend(
        store,
        block_id=_BLOCK_ID,
        day=_DAY,
        target_market=MarketSegment.EXPORT_EU,
        days_until_harvest=_HARVEST_DAYS,
    )
    mandi = recommend(
        store,
        block_id=_BLOCK_ID,
        day=_DAY,
        target_market=MarketSegment.DOMESTIC_MANDI,
        days_until_harvest=_HARVEST_DAYS,
    )
    # Equal-or-different is fine; what matters is both ran cleanly.
    assert eu.primary_pathogen == mandi.primary_pathogen
    # The PPI should be identical (same observations)
    assert eu.ppi == pytest.approx(mandi.ppi)
