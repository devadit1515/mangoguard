"""Tests for the MRL tables loader."""

from __future__ import annotations

import pytest

from mangoguard.recommend import mrl_loader as _mrl_loader_module
from mangoguard.recommend.mrl_loader import (
    default_floor,
    listed_ingredients,
    load_mrl_table,
    lookup_mrl,
    reset_cache,
    strictest_mrl,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    """Drop the lru_cache between tests so each test gets a fresh load."""
    reset_cache()
    yield
    reset_cache()


def test_load_eu_table_returns_metadata_and_limits():
    table = load_mrl_table("eu")
    assert "metadata" in table
    assert "limits" in table
    assert table["metadata"]["crop"] == "Mango"


def test_load_japan_table_returns_metadata_and_limits():
    table = load_mrl_table("japan")
    assert "limits" in table
    assert table["metadata"]["crop"] == "Mango"


def test_load_fssai_table_returns_metadata_and_limits():
    table = load_mrl_table("fssai")
    assert "limits" in table


def test_load_codex_table_returns_metadata_and_limits():
    table = load_mrl_table("codex")
    assert "limits" in table


def test_load_buyer_specific_table_has_empty_limits_by_default():
    """Buyer-specific table is an empty placeholder until per-buyer specs land."""
    table = load_mrl_table("buyer_specific")
    assert table.get("limits") == {}


def test_load_unknown_table_raises_file_not_found():
    with pytest.raises(FileNotFoundError, match="MRL table not found"):
        load_mrl_table("mars_alimentarius")


def test_lookup_mrl_returns_float_for_known_ingredient():
    eu_hexaconazole = lookup_mrl("eu", "hexaconazole")
    assert isinstance(eu_hexaconazole, float)
    assert 0.0 < eu_hexaconazole < 100.0


def test_lookup_mrl_case_insensitive():
    a = lookup_mrl("eu", "hexaconazole")
    b = lookup_mrl("eu", "HEXACONAZOLE")
    c = lookup_mrl("eu", "  Hexaconazole  ")
    assert a == b == c


def test_lookup_mrl_unknown_ingredient_returns_none():
    assert lookup_mrl("eu", "completely_made_up_compound") is None


def test_lookup_mrl_buyer_specific_returns_none_when_empty():
    """Empty placeholder table: every lookup returns None."""
    assert lookup_mrl("buyer_specific", "hexaconazole") is None


def test_default_floor_returns_001_for_known_tables():
    """All 5 placeholder tables document a 0.01 mg/kg default floor."""
    for market in ("eu", "japan", "codex", "fssai", "buyer_specific"):
        assert default_floor(market) == pytest.approx(0.01)


def test_listed_ingredients_includes_common_konkan_pesticides():
    eu_ingredients = listed_ingredients("eu")
    assert "hexaconazole" in eu_ingredients
    assert "imidacloprid" in eu_ingredients
    assert "carbendazim" in eu_ingredients
    assert "mancozeb" in eu_ingredients


def test_strictest_mrl_picks_minimum_across_chain():
    """EU + Japan chain: take the stricter of the two MRLs."""
    eu_mrl = lookup_mrl("eu", "imidacloprid")
    japan_mrl = lookup_mrl("japan", "imidacloprid")
    strict = strictest_mrl(["eu", "japan"], "imidacloprid")
    assert strict is not None
    assert strict == min(eu_mrl, japan_mrl)


def test_strictest_mrl_handles_one_table_missing_ingredient():
    """An ingredient absent from every table -> None."""
    nonexistent = strictest_mrl(["eu", "japan", "fssai"], "unobtainium")
    assert nonexistent is None


def test_strictest_mrl_empty_chain_returns_none():
    assert strictest_mrl([], "hexaconazole") is None


def test_load_malformed_yaml_raises_value_error(tmp_path, monkeypatch):
    """A YAML parse failure surfaces as a clear ValueError."""
    bad_yaml = tmp_path / "broken.yaml"
    bad_yaml.write_text("limits: {hexaconazole: [\n", encoding="utf-8")

    monkeypatch.setattr(_mrl_loader_module, "_table_path", lambda _market: bad_yaml)
    reset_cache()

    with pytest.raises(ValueError, match="malformed YAML"):
        load_mrl_table("eu")


def test_load_yaml_missing_limits_key_raises_value_error(tmp_path, monkeypatch):
    bad_yaml = tmp_path / "no_limits.yaml"
    bad_yaml.write_text("metadata:\n  crop: Mango\n", encoding="utf-8")
    monkeypatch.setattr(_mrl_loader_module, "_table_path", lambda _market: bad_yaml)
    reset_cache()
    with pytest.raises(ValueError, match="missing required top-level 'limits' key"):
        load_mrl_table("eu")


def test_caching_avoids_repeated_parse(monkeypatch):
    """Second load uses the lru_cache without re-opening the file."""
    load_mrl_table("eu")  # warm the cache
    call_count = [0]
    original_open = open

    def counting_open(*args, **kwargs):
        call_count[0] += 1
        return original_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", counting_open)
    load_mrl_table("eu")
    load_mrl_table("eu")
    assert call_count[0] == 0


def test_eu_is_at_least_as_strict_as_codex_for_common_ingredients():
    """Sanity check: EU MRLs should be <= Codex MRLs for most ingredients."""
    stricter_count = 0
    looser_count = 0
    shared = listed_ingredients("eu") & listed_ingredients("codex")
    for ingredient in shared:
        eu = lookup_mrl("eu", ingredient)
        codex = lookup_mrl("codex", ingredient)
        if eu is None or codex is None:
            continue
        if eu < codex:
            stricter_count += 1
        elif eu > codex:
            looser_count += 1
    assert stricter_count >= looser_count, (
        f"expected EU >= Codex strictness, got stricter={stricter_count} " f"looser={looser_count}"
    )
