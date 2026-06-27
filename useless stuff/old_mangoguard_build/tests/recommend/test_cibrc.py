"""Tests for the CIB&RC registered-pesticide registry."""

from __future__ import annotations

import pytest

from mangoguard.recommend import cibrc as _cibrc_module
from mangoguard.recommend.cibrc import (
    CIBRCEntry,
    all_entries,
    get_phi_days,
    is_registered,
    max_phi_days,
    pesticides_for_pathogen,
    registered_ingredients,
    reset_cache,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    reset_cache()
    yield
    reset_cache()


def test_csv_loads_at_least_15_entries():
    entries = all_entries()
    assert len(entries) >= 15


def test_every_entry_has_expected_fields():
    for e in all_entries():
        assert isinstance(e, CIBRCEntry)
        assert e.active_ingredient
        assert e.target_pest_class
        assert isinstance(e.phi_days, int)
        assert e.phi_days >= 0


def test_active_ingredients_normalized_to_lowercase():
    for e in all_entries():
        assert e.active_ingredient == e.active_ingredient.lower()


def test_pesticides_for_anthracnose_returns_at_least_one():
    rows = pesticides_for_pathogen("anthracnose")
    assert len(rows) >= 1
    assert all(e.target_pest_class == "anthracnose" for e in rows)


def test_pesticides_for_powdery_mildew_returns_at_least_one():
    rows = pesticides_for_pathogen("powdery_mildew")
    assert len(rows) >= 1


def test_pesticides_for_hopper_returns_at_least_one():
    rows = pesticides_for_pathogen("hopper")
    assert len(rows) >= 1


def test_pesticides_lookup_case_insensitive():
    a = pesticides_for_pathogen("anthracnose")
    b = pesticides_for_pathogen("Anthracnose")
    c = pesticides_for_pathogen("  ANTHRACNOSE  ")
    assert len(a) == len(b) == len(c)


def test_pesticides_for_unknown_pathogen_returns_empty():
    assert pesticides_for_pathogen("dragon_pox") == []


def test_get_phi_days_returns_int_for_known_ingredient():
    phi = get_phi_days("hexaconazole")
    assert phi is not None
    assert phi > 0


def test_get_phi_days_for_unknown_returns_none():
    assert get_phi_days("unobtainium") is None


def test_max_phi_days_at_least_min_phi_days():
    """max_phi_days must always be >= min_phi_days for ingredients with multiple regs."""
    for ai in registered_ingredients():
        min_phi = get_phi_days(ai)
        max_phi = max_phi_days(ai)
        assert min_phi is not None and max_phi is not None
        assert max_phi >= min_phi


def test_is_registered_for_known_ingredient_true():
    assert is_registered("hexaconazole") is True
    assert is_registered("HEXACONAZOLE") is True
    assert is_registered("  hexaconazole  ") is True


def test_is_registered_for_unknown_false():
    assert is_registered("dragon_powder") is False


def test_registered_ingredients_includes_common_konkan_aichoices():
    ingredients = registered_ingredients()
    # The Konkan-Alphonso decision tree needs at least these:
    assert "hexaconazole" in ingredients
    assert "imidacloprid" in ingredients
    assert "carbendazim" in ingredients
    assert "sulphur" in ingredients


def test_missing_csv_raises_file_not_found(tmp_path, monkeypatch):
    """If the CSV file is missing, the load surfaces a clear error."""
    monkeypatch.setattr(_cibrc_module, "_csv_path", lambda: tmp_path / "missing.csv")
    reset_cache()
    with pytest.raises(FileNotFoundError, match="CIB&RC registry not found"):
        all_entries()


def test_malformed_row_dropped_with_warning(tmp_path, monkeypatch, caplog):
    bad_csv = (
        "active_ingredient,formulation,dose_per_liter_water,target_pest_class,phi_days,"
        "registration_status,notes\n"
        "hexaconazole,5 EC,2 ml/L,anthracnose,not_an_int,registered,\n"
        "carbendazim,50 WP,1 g/L,anthracnose,40,registered,\n"
    )
    bad_path = tmp_path / "bad.csv"
    bad_path.write_text(bad_csv, encoding="utf-8")
    monkeypatch.setattr(_cibrc_module, "_csv_path", lambda: bad_path)
    reset_cache()
    with caplog.at_level("WARNING"):
        entries = all_entries()
    assert len(entries) == 1
    assert entries[0].active_ingredient == "carbendazim"
    assert any("CIB&RC" in r.message for r in caplog.records)
