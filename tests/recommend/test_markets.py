"""Tests for the MarketSegment enum + segment-to-MRL mapping."""

from __future__ import annotations

import pytest

from mangoguard.recommend.markets import (
    MARKET_MRL_TABLE,
    MarketSegment,
    mrl_tables_for,
)


def test_enum_covers_four_segments():
    assert len(MarketSegment) == 4


def test_enum_string_values_are_stable_slugs():
    """The string values are persisted in CSV / YAML configs; pin them."""
    assert MarketSegment.EXPORT_EU.value == "export_eu_japan_us"
    assert MarketSegment.EXPORT_GULF.value == "export_gulf_me_seasia"
    assert MarketSegment.DOMESTIC_RETAIL.value == "domestic_retail_processor"
    assert MarketSegment.DOMESTIC_MANDI.value == "domestic_mandi"


def test_each_segment_has_at_least_one_mrl_table():
    for segment in MarketSegment:
        assert len(MARKET_MRL_TABLE[segment]) >= 1


def test_export_eu_chain_includes_eu_and_japan():
    assert "eu" in MARKET_MRL_TABLE[MarketSegment.EXPORT_EU]
    assert "japan" in MARKET_MRL_TABLE[MarketSegment.EXPORT_EU]


def test_domestic_mandi_uses_only_fssai():
    assert MARKET_MRL_TABLE[MarketSegment.DOMESTIC_MANDI] == ["fssai"]


def test_mrl_tables_for_returns_chain_list():
    chain = mrl_tables_for(MarketSegment.EXPORT_EU)
    assert isinstance(chain, list)
    assert chain == ["eu", "japan"]


def test_mrl_tables_for_returns_a_copy_not_internal_reference():
    """Caller mutation must not corrupt the global MARKET_MRL_TABLE."""
    chain = mrl_tables_for(MarketSegment.EXPORT_EU)
    chain.append("hacked")
    assert "hacked" not in MARKET_MRL_TABLE[MarketSegment.EXPORT_EU]


def test_str_subclass_allows_yaml_serialization():
    """Because MarketSegment subclasses str, it round-trips through YAML/JSON cleanly."""
    assert MarketSegment.EXPORT_EU == "export_eu_japan_us"
    # The .value form is what gets written to disk.
    assert MarketSegment.DOMESTIC_MANDI.value == "domestic_mandi"


def test_export_segments_stricter_than_domestic():
    """Sanity: export chains include at least one strict table (eu/japan/codex)."""
    eu_chain = MARKET_MRL_TABLE[MarketSegment.EXPORT_EU]
    gulf_chain = MARKET_MRL_TABLE[MarketSegment.EXPORT_GULF]
    assert any(t in {"eu", "japan", "codex"} for t in eu_chain)
    assert any(t in {"eu", "japan", "codex"} for t in gulf_chain)


def test_mrl_tables_for_unknown_segment_raises_key_error(monkeypatch):
    """Defensive guard: a future enum addition without mapping must fail loudly."""
    monkeypatch.delitem(MARKET_MRL_TABLE, MarketSegment.EXPORT_GULF)
    with pytest.raises(KeyError, match="no MRL-table chain"):
        mrl_tables_for(MarketSegment.EXPORT_GULF)
