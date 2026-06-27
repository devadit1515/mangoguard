"""Simulation: panel shape, determinism, independence, and tier behaviour."""

from __future__ import annotations

import pandas as pd
import pytest

from aamrakshak.eval.metrics import roc_auc
from aamrakshak.riskengine.anthracnose import AnthracnoseInputs, anthracnose_risk
from aamrakshak.sim.outbreaks import add_outbreak_labels
from aamrakshak.sim.sensors import _vec_anthracnose_risk, tier_risk_scores
from aamrakshak.sim.weather import SEASON_DAYS, generate_panel


@pytest.fixture(scope="module")
def panel():
    p = generate_panel(seed=20260627, n_seasons=2, n_blocks=3)
    return add_outbreak_labels(p, 20260627)


def test_panel_shape_and_columns(panel):
    assert len(panel) == 2 * 2 * 3 * SEASON_DAYS  # regions * seasons * blocks * days
    for col in ["t_max", "t_min", "rh_morning", "leaf_wetness_true", "outbreak", "district_rh"]:
        assert col in panel.columns


def test_generation_is_deterministic():
    a = generate_panel(seed=42, n_seasons=1, n_blocks=2)
    b = generate_panel(seed=42, n_seasons=1, n_blocks=2)
    pd.testing.assert_frame_equal(a, b)


def test_outbreak_rate_reasonable(panel):
    rate = panel["outbreak"].mean()
    assert 0.15 < rate < 0.55


def test_humid_region_has_more_outbreaks(panel):
    konkan = panel.loc[panel["region"] == "konkan_humid", "outbreak"].mean()
    gujarat = panel.loc[panel["region"] == "gujarat_drier", "outbreak"].mean()
    assert konkan > gujarat


def test_vectorised_matches_scalar(panel):
    # The vectorised scorer must equal the scalar anthracnose_risk row-by-row.
    sample = panel.head(50)
    vec = _vec_anthracnose_risk(
        sample["t_max"].to_numpy(),
        sample["t_min"].to_numpy(),
        sample["rh_morning"].to_numpy(),
        sample["leaf_wetness_true"].to_numpy(),
        sample["sunshine"].to_numpy(),
        sample["wind"].to_numpy(),
    )
    for i, (_, row) in enumerate(sample.iterrows()):
        scalar = anthracnose_risk(
            AnthracnoseInputs(
                t_max_c=row["t_max"],
                t_min_c=row["t_min"],
                rh_morning_pct=row["rh_morning"],
                leaf_wetness_hr=row["leaf_wetness_true"],
                sunshine_hr=row["sunshine"],
                wind_speed_ms=row["wind"],
            )
        )
        assert vec[i] == pytest.approx(scalar, abs=1e-12)


def test_tier_scores_in_unit_interval(panel):
    for tier in ("calendar", "free", "node", "commercial"):
        s = tier_risk_scores(panel, tier, seed=1)
        assert s.min() >= 0.0 and s.max() <= 1.0


def test_node_tier_beats_free_tier(panel):
    # The central claim, as a regression test: measuring leaf wetness (node)
    # discriminates better than estimating it from RH (free feed).
    y = panel["outbreak"].to_numpy()
    auc_node = roc_auc(y, tier_risk_scores(panel, "node", seed=1))
    auc_free = roc_auc(y, tier_risk_scores(panel, "free", seed=1))
    assert auc_node > auc_free + 0.05


def test_unknown_tier_raises(panel):
    with pytest.raises(ValueError):
        tier_risk_scores(panel, "satellite", seed=1)
