"""End-to-end smoke test exercising the full MangoGuard stack (Plan 6 Task 12).

Walks through the production-time decision flow once against a synthetic
FeedStore + all real loaders (CIB&RC, MRL tables, RASFF, pesticide
metadata, ranker, baseline schedule, evaluators). The goal is to catch
upstream/downstream interface drift before tagging a release.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pandas as pd
import pytest

from mangoguard.evaluation.baseline_schedule import (
    get_baseline_recommendation,
)
from mangoguard.evaluation.rasff_counterfactual import (
    evaluate_rasff_counterfactual,
)
from mangoguard.recommend.markets import MarketSegment
from mangoguard.recommend.recommend import recommend
from mangoguard.risk.ppi import compute_ppi
from mangoguard.schema import BlockObservation, ConnectorSource

_DAY = date(2025, 7, 15)
_BLOCK_ID = "ratnagiri_block_A"
_TALUKA_HOPPER = "ratnagiri_hopper"


def _imd_row(block_id: str, when: datetime, **kw) -> BlockObservation:
    return BlockObservation(block_id=block_id, ts=when, source=ConnectorSource.IMD, **kw)


def _seed_full(store) -> None:
    """30 days warm + humid IMD + 4 NDRE + 1 CROPSAP -> realistic Module 3 inputs."""
    base = datetime.combine(_DAY - timedelta(days=29), datetime.min.time(), tzinfo=timezone.utc)
    for i in range(30):
        store.insert(
            _imd_row(
                _BLOCK_ID,
                base + timedelta(days=i),
                t_air_c=27.5 + i * 0.05,
                rh_pct=93.0,
                leaf_wetness_hr=8.5,
                wind_speed_ms=1.0,
                solar_w_m2=70.0,
            )
        )
    for offset, ndre in zip((28, 21, 14, 7), (0.55, 0.52, 0.48, 0.42), strict=True):
        store.insert(
            BlockObservation(
                block_id=_BLOCK_ID,
                ts=base + timedelta(days=offset),
                source=ConnectorSource.SENTINEL2,
                ndre=ndre,
            )
        )
    store.insert(
        BlockObservation(
            block_id=_TALUKA_HOPPER,
            ts=datetime.combine(_DAY, datetime.min.time(), tzinfo=timezone.utc),
            source=ConnectorSource.CROPSAP,
            cropsap_pest_pressure=40.0,
        )
    )


def test_e2e_ppi_and_recommendation(store):
    _seed_full(store)
    components = compute_ppi(store, _BLOCK_ID, _DAY)
    assert 0.0 <= components["ppi"] <= 100.0
    result = recommend(
        store,
        block_id=_BLOCK_ID,
        day=_DAY,
        target_market=MarketSegment.DOMESTIC_MANDI,
        days_until_harvest=60,
    )
    assert result.block_id == _BLOCK_ID
    assert result.rationale


def test_e2e_baseline_schedule_lookup():
    # ISO week 7 = flowering: CISH baseline recommends carbendazim for anthracnose
    bl = get_baseline_recommendation("icar_cish", iso_week=7, pathogen="anthracnose")
    assert bl is not None
    assert bl == "carbendazim"


def test_e2e_rasff_counterfactual_runs():
    """RASFF counterfactual must run end-to-end against the placeholder data."""
    rejections = pd.DataFrame(
        [
            {"date": "2023-04-05", "active_ingredient": "chlorpyrifos", "destination": "EU"},
            {"date": "2023-05-18", "active_ingredient": "carbendazim", "destination": "EU"},
        ]
    )
    result = evaluate_rasff_counterfactual(rejections, cutoff=0.10)
    assert "prevention_rate_mangoguard" in result
    assert 0.0 <= result["prevention_rate_mangoguard"] <= 1.0


@pytest.mark.parametrize(
    "segment",
    [
        MarketSegment.EXPORT_EU,
        MarketSegment.EXPORT_GULF,
        MarketSegment.DOMESTIC_RETAIL,
        MarketSegment.DOMESTIC_MANDI,
    ],
)
def test_e2e_recommend_per_segment_returns_recommendation(store, segment):
    _seed_full(store)
    result = recommend(
        store,
        block_id=_BLOCK_ID,
        day=_DAY,
        target_market=segment,
        days_until_harvest=60,
    )
    assert result.target_market == segment
    assert result.ppi >= 0.0
