"""Shared pytest fixtures."""

from datetime import datetime, timezone

import pytest

from mangoguard.schema import BlockObservation, ConnectorSource
from mangoguard.store import FeedStore


@pytest.fixture
def store() -> FeedStore:
    return FeedStore(":memory:")


@pytest.fixture
def sample_observation() -> BlockObservation:
    return BlockObservation(
        block_id="B3",
        ts=datetime(2026, 7, 12, 10, 30, tzinfo=timezone.utc),
        source=ConnectorSource.PESSL,
        t_air_c=28.4,
        rh_pct=87.2,
        leaf_wetness_hr=4.5,
        precip_mm=1.2,
    )


@pytest.fixture
def sample_observations() -> list[BlockObservation]:
    base = datetime(2026, 7, 12, tzinfo=timezone.utc)
    return [
        BlockObservation(
            block_id="B1",
            ts=base.replace(hour=h),
            source=ConnectorSource.IMD,
            t_air_c=24.0 + h * 0.3,
            rh_pct=80.0 + h * 0.1,
        )
        for h in range(0, 24, 6)
    ]
