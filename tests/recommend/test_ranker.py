"""Tests for the pesticide ranker."""

from __future__ import annotations

import math

import pytest

from mangoguard.recommend.pesticide_metadata import PesticideMetadata
from mangoguard.recommend.ranker import rank_candidates, top_n


def _mk(
    name: str,
    *,
    half_life: float,
    cost: float,
    efficacy: float,
    pathogen: str = "anthracnose",
) -> PesticideMetadata:
    return PesticideMetadata(
        active_ingredient=name,
        residue_half_life_days=half_life,
        cost_per_acre_inr=cost,
        efficacy_per_pathogen={pathogen: efficacy},
        source="test",
    )


def test_high_efficacy_short_halflife_low_cost_ranks_first():
    best = _mk("best", half_life=5, cost=100, efficacy=0.95)
    worse_high_cost = _mk("expensive", half_life=5, cost=500, efficacy=0.95)
    worse_long_halflife = _mk("persistent", half_life=30, cost=100, efficacy=0.95)
    worse_low_efficacy = _mk("weak", half_life=5, cost=100, efficacy=0.20)
    ranked = rank_candidates(
        [worse_high_cost, worse_long_halflife, worse_low_efficacy, best],
        pathogen="anthracnose",
    )
    assert ranked[0].active_ingredient == "best"


def test_long_halflife_demotes_rank():
    short = _mk("short", half_life=5, cost=200, efficacy=0.80)
    long_ = _mk("long", half_life=40, cost=200, efficacy=0.80)
    ranked = rank_candidates([long_, short], pathogen="anthracnose")
    assert ranked[0].active_ingredient == "short"
    assert ranked[1].active_ingredient == "long"


def test_high_cost_demotes_rank():
    cheap = _mk("cheap", half_life=10, cost=100, efficacy=0.80)
    expensive = _mk("expensive", half_life=10, cost=600, efficacy=0.80)
    ranked = rank_candidates([expensive, cheap], pathogen="anthracnose")
    assert ranked[0].active_ingredient == "cheap"


def test_zero_efficacy_pathogen_ranks_last():
    """If a candidate has no efficacy vs the target pathogen, it must rank below
    any candidate with positive efficacy."""
    hopper_targeted = _mk(
        "imidacloprid_like",
        half_life=10,
        cost=200,
        efficacy=0.85,
        pathogen="hopper",
    )
    fungicide = _mk("hexaconazole_like", half_life=10, cost=200, efficacy=0.85)
    ranked = rank_candidates([hopper_targeted, fungicide], pathogen="anthracnose")
    # fungicide ranks first because hopper_targeted has 0 anthracnose efficacy
    assert ranked[0].active_ingredient == "hexaconazole_like"


def test_log_score_formula_matches_spec():
    """Verify the exact formula: log(eff+eps) - log(hl+1) - log(cost+1)."""
    cand = _mk("test", half_life=10, cost=200, efficacy=0.80)
    ranked = rank_candidates([cand], pathogen="anthracnose")
    expected = math.log(0.80 + 1e-6) - math.log(11) - math.log(201)
    assert ranked[0].log_score == pytest.approx(expected, rel=1e-6)


def test_ties_broken_by_lower_half_life():
    a = _mk("a", half_life=20, cost=200, efficacy=0.80)
    b = _mk("b", half_life=5, cost=200, efficacy=0.80)
    # b should win the tie even if log_scores are mathematically identical
    # (they aren't because half_life enters log_score -- but the sort key
    # still applies a secondary order)
    ranked = rank_candidates([a, b], pathogen="anthracnose")
    assert ranked[0].active_ingredient == "b"


def test_top_n_returns_n_or_fewer():
    cands = [_mk(f"c{i}", half_life=10, cost=200, efficacy=0.5 + i * 0.05) for i in range(8)]
    top = top_n(cands, pathogen="anthracnose", n=3)
    assert len(top) == 3


def test_top_n_with_n_larger_than_pool_returns_all():
    cands = [_mk(f"c{i}", half_life=10, cost=200, efficacy=0.5) for i in range(3)]
    top = top_n(cands, pathogen="anthracnose", n=10)
    assert len(top) == 3


def test_empty_input_returns_empty():
    assert rank_candidates([], pathogen="anthracnose") == []


def test_log_score_finite_for_zero_efficacy():
    """With efficacy=0 we add EPSILON to avoid log(0) -> -inf. Verify finite."""
    zero = _mk("zero", half_life=10, cost=200, efficacy=0.0)
    ranked = rank_candidates([zero], pathogen="anthracnose")
    assert math.isfinite(ranked[0].log_score)
