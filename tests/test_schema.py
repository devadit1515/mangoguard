"""Tests for the unified per-block-per-timestamp observation schema."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from mangoguard.schema import BlockObservation, ConnectorSource


def test_block_observation_minimal_required_fields():
    obs = BlockObservation(
        block_id="B3",
        ts=datetime(2026, 7, 12, 10, 30, tzinfo=timezone.utc),
        source=ConnectorSource.IMD,
    )
    assert obs.block_id == "B3"
    assert obs.source == ConnectorSource.IMD
    assert obs.t_air_c is None
    assert obs.rh_pct is None


def test_block_observation_all_fields_populated():
    obs = BlockObservation(
        block_id="B1",
        ts=datetime(2026, 7, 12, 10, 30, tzinfo=timezone.utc),
        source=ConnectorSource.PESSL,
        t_air_c=28.4,
        rh_pct=87.2,
        leaf_wetness_hr=4.5,
        precip_mm=1.2,
        wind_speed_ms=2.1,
        solar_w_m2=412.0,
        soil_moisture_pct=34.5,
        ndvi=0.71,
        ndre=0.42,
        ndmi=0.18,
        plantix_diagnosis_class="anthracnose",
        notes="post-rain sample",
    )
    assert obs.t_air_c == 28.4
    assert obs.ndre == 0.42
    assert obs.plantix_diagnosis_class == "anthracnose"


def test_block_observation_rejects_naive_datetime():
    with pytest.raises(ValidationError):
        BlockObservation(
            block_id="B3",
            ts=datetime(2026, 7, 12, 10, 30),  # naive — no tzinfo
            source=ConnectorSource.IMD,
        )


def test_block_observation_rejects_out_of_range_rh():
    with pytest.raises(ValidationError):
        BlockObservation(
            block_id="B3",
            ts=datetime(2026, 7, 12, tzinfo=timezone.utc),
            source=ConnectorSource.IMD,
            rh_pct=150.0,
        )


def test_block_observation_rejects_out_of_range_ndvi():
    with pytest.raises(ValidationError):
        BlockObservation(
            block_id="B3",
            ts=datetime(2026, 7, 12, tzinfo=timezone.utc),
            source=ConnectorSource.SENTINEL2,
            ndvi=1.5,
        )


def test_connector_source_enum_covers_all_planned_sources():
    expected = {
        "FYLLO",
        "FASAL",
        "PESSL",
        "IMD",
        "PLANTIX",
        "AGMARKNET",
        "DBSKKV",
        "CROPSAP",
        "SENTINEL2",
        "CSV_FALLBACK",
    }
    assert {s.name for s in ConnectorSource} == expected


def test_block_observation_accepts_valid_boundary_values():
    """Confirm `ge`/`le` bounds are inclusive — not `gt`/`lt`."""
    obs_low = BlockObservation(
        block_id="B1",
        ts=datetime(2026, 7, 12, tzinfo=timezone.utc),
        source=ConnectorSource.IMD,
        rh_pct=0.0,
        ndvi=-1.0,
        ndre=-1.0,
        ndmi=-1.0,
        leaf_wetness_hr=0.0,
        soil_moisture_pct=0.0,
    )
    assert obs_low.rh_pct == 0.0
    assert obs_low.ndvi == -1.0

    obs_high = BlockObservation(
        block_id="B1",
        ts=datetime(2026, 7, 12, tzinfo=timezone.utc),
        source=ConnectorSource.IMD,
        rh_pct=100.0,
        ndvi=1.0,
        ndre=1.0,
        ndmi=1.0,
        leaf_wetness_hr=24.0,
        soil_moisture_pct=100.0,
    )
    assert obs_high.rh_pct == 100.0
    assert obs_high.ndvi == 1.0
    assert obs_high.leaf_wetness_hr == 24.0


def test_block_observation_is_frozen():
    """Pydantic v2 `frozen=True` must reject mutation after construction."""
    obs = BlockObservation(
        block_id="B1",
        ts=datetime(2026, 7, 12, tzinfo=timezone.utc),
        source=ConnectorSource.IMD,
        t_air_c=25.0,
    )
    with pytest.raises(ValidationError):
        obs.t_air_c = 99.0  # type: ignore[misc]


def test_block_observation_rejects_extra_fields():
    """`extra="forbid"` must reject unknown fields to catch connector bugs early."""
    with pytest.raises(ValidationError):
        BlockObservation(
            block_id="B1",
            ts=datetime(2026, 7, 12, tzinfo=timezone.utc),
            source=ConnectorSource.IMD,
            unknown_vendor_field="oops",  # type: ignore[call-arg]
        )
