"""Tests for the pesticide metadata loader."""

from __future__ import annotations

import pytest

from mangoguard.recommend import pesticide_metadata as _metadata_module
from mangoguard.recommend.cibrc import (
    registered_ingredients,
)
from mangoguard.recommend.cibrc import (
    reset_cache as reset_cibrc_cache,
)
from mangoguard.recommend.pesticide_metadata import (
    PesticideMetadata,
    all_metadata,
    listed_ingredients,
    lookup,
    reset_cache,
)


@pytest.fixture(autouse=True)
def _clear_caches():
    reset_cache()
    reset_cibrc_cache()
    yield
    reset_cache()
    reset_cibrc_cache()


def test_yaml_loads_at_least_15_entries():
    entries = all_metadata()
    assert len(entries) >= 15


def test_every_entry_has_expected_fields():
    for e in all_metadata():
        assert isinstance(e, PesticideMetadata)
        assert e.active_ingredient == e.active_ingredient.lower()
        assert e.residue_half_life_days > 0
        assert e.cost_per_acre_inr > 0
        assert isinstance(e.efficacy_per_pathogen, dict)


def test_efficacies_in_0_1():
    for e in all_metadata():
        for pathogen, efficacy in e.efficacy_per_pathogen.items():
            assert 0.0 <= efficacy <= 1.0, f"{e.active_ingredient}/{pathogen}: {efficacy}"


def test_metadata_subset_of_cibrc_registry():
    """Plan 4 Task 10 Step 2: every metadata entry must be a CIB&RC-registered AI.

    The metadata file attaches numeric attributes (half-life, cost, efficacy) to
    each CIB&RC-registered ingredient -- so the metadata's AI universe is a
    subset of the registry's AI universe.
    """
    metadata_ais = listed_ingredients()
    cibrc_ais = registered_ingredients()
    extras = metadata_ais - cibrc_ais
    assert not extras, f"Metadata has AIs missing from CIB&RC: {extras}"


def test_lookup_returns_entry_for_known_ai():
    entry = lookup("hexaconazole")
    assert entry is not None
    assert entry.active_ingredient == "hexaconazole"


def test_lookup_case_insensitive():
    a = lookup("HEXACONAZOLE")
    b = lookup("hexaconazole")
    c = lookup("  hexaconazole  ")
    assert a is not None and b is not None and c is not None
    assert a.active_ingredient == b.active_ingredient == c.active_ingredient


def test_lookup_for_unknown_returns_none():
    assert lookup("unobtainium") is None


def test_efficacy_against_returns_float_in_0_1():
    entry = lookup("hexaconazole")
    assert entry is not None
    assert 0.0 <= entry.efficacy_against("anthracnose") <= 1.0


def test_efficacy_against_unknown_pathogen_returns_zero():
    entry = lookup("hexaconazole")
    assert entry is not None
    assert entry.efficacy_against("dragon_pox") == 0.0


def test_efficacy_against_case_insensitive():
    entry = lookup("hexaconazole")
    assert entry is not None
    a = entry.efficacy_against("ANTHRACNOSE")
    b = entry.efficacy_against("anthracnose")
    assert a == b


def test_missing_yaml_raises_file_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(_metadata_module, "_yaml_path", lambda: tmp_path / "missing.yaml")
    reset_cache()
    with pytest.raises(FileNotFoundError, match="Pesticide metadata YAML not found"):
        all_metadata()


def test_malformed_yaml_raises_value_error(tmp_path, monkeypatch):
    bad = tmp_path / "bad.yaml"
    bad.write_text("not_a_pesticides_root: []\n", encoding="utf-8")
    monkeypatch.setattr(_metadata_module, "_yaml_path", lambda: bad)
    reset_cache()
    with pytest.raises(ValueError, match="Malformed pesticide metadata YAML"):
        all_metadata()


def test_anthracnose_top_ranked_have_nonzero_efficacy():
    """Domain check: at least one fungicide must score >= 0.7 vs anthracnose."""
    entries = all_metadata()
    best = max(e.efficacy_against("anthracnose") for e in entries)
    assert best >= 0.7


def test_hopper_top_ranked_have_nonzero_efficacy():
    entries = all_metadata()
    best = max(e.efficacy_against("hopper") for e in entries)
    assert best >= 0.7


def test_powdery_mildew_top_ranked_have_nonzero_efficacy():
    entries = all_metadata()
    best = max(e.efficacy_against("powdery_mildew") for e in entries)
    assert best >= 0.7
