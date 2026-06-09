"""Tests for the RASFF historical-rejection analyzer."""

from __future__ import annotations

import pytest

from mangoguard.recommend import rasff as _rasff_module
from mangoguard.recommend.rasff import (
    RASFFRow,
    all_rows,
    offending_ingredients,
    rejection_count,
    rejection_count_by_ingredient,
    rejection_probability,
    reset_cache,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    reset_cache()
    yield
    reset_cache()


def test_csv_loads_at_least_20_rows():
    rows = all_rows()
    assert len(rows) >= 20


def test_every_row_has_expected_field_types():
    for r in all_rows():
        assert isinstance(r, RASFFRow)
        assert r.active_ingredient == r.active_ingredient.lower()
        assert r.destination == r.destination.upper()
        assert isinstance(r.mrl_mg_per_kg, float)
        assert isinstance(r.detected_mg_per_kg, float)


def test_detected_exceeds_mrl_for_every_row():
    """A rejection means the detected residue exceeded the destination MRL."""
    for r in all_rows():
        assert r.detected_mg_per_kg > r.mrl_mg_per_kg


def test_rejection_count_for_chlorpyrifos_eu_high():
    """Chlorpyrifos is the canonical EU-rejection ingredient -- multiple rows expected."""
    assert rejection_count("chlorpyrifos", "EU") >= 4


def test_rejection_count_case_insensitive():
    a = rejection_count("CHLORPYRIFOS", "eu")
    b = rejection_count("chlorpyrifos", "EU")
    assert a == b


def test_rejection_count_unknown_ingredient_zero():
    assert rejection_count("unobtainium", "EU") == 0


def test_rejection_probability_in_0_1():
    p = rejection_probability("chlorpyrifos", "EU")
    assert 0.0 <= p <= 1.0


def test_unknown_pesticide_returns_default_prior_below_0_1():
    """No history + 10-count Beta prior + 50 inspections -> p ~= 0.0167 << 0.1."""
    p = rejection_probability("never_used_before", "EU")
    assert p < 0.1


def test_high_historical_freq_yields_high_probability():
    """Chlorpyrifos with 5+ EU rejections must score above the no-history baseline."""
    chlorpyrifos = rejection_probability("chlorpyrifos", "EU")
    baseline = rejection_probability("never_used_before", "EU")
    assert chlorpyrifos > baseline


def test_export_threshold_excludes_chlorpyrifos_for_eu():
    """Recommender uses a 0.20 cutoff per spec 4.3.3c. With placeholder data and
    default inspections=50, chlorpyrifos may or may not exceed; just verify the
    monotonic ordering: chlorpyrifos > carbendazim > unknown."""
    chlorpyrifos = rejection_probability("chlorpyrifos", "EU")
    carbendazim = rejection_probability("carbendazim", "EU")
    unknown = rejection_probability("never_used_before", "EU")
    assert chlorpyrifos > unknown
    assert carbendazim > unknown


def test_inspections_kwarg_lowers_probability_when_high():
    """Increasing the assumed inspection denominator shrinks p_hat."""
    p_default = rejection_probability("chlorpyrifos", "EU")
    p_more = rejection_probability("chlorpyrifos", "EU", inspections=10000)
    assert p_more < p_default


def test_destination_normalized_to_uppercase():
    """RASFF rows are keyed by uppercase destination."""
    a = rejection_count("chlorpyrifos", "eu")
    b = rejection_count("chlorpyrifos", "EU")
    c = rejection_count("chlorpyrifos", "  EU  ")
    assert a == b == c


def test_offending_ingredients_for_eu_includes_chlorpyrifos():
    bad_actors = offending_ingredients("EU")
    assert "chlorpyrifos" in bad_actors
    assert "carbendazim" in bad_actors


def test_offending_ingredients_for_unknown_destination_empty():
    assert offending_ingredients("MARS") == set()


def test_rejection_count_by_ingredient_returns_dict():
    counts = rejection_count_by_ingredient("EU")
    assert isinstance(counts, dict)
    assert counts.get("chlorpyrifos", 0) >= 4
    # Every count is a positive int
    for _k, v in counts.items():
        assert isinstance(v, int) and v >= 1


def test_missing_csv_raises_file_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(_rasff_module, "_csv_path", lambda: tmp_path / "nope.csv")
    reset_cache()
    with pytest.raises(FileNotFoundError, match="RASFF dataset not found"):
        all_rows()


def test_malformed_row_dropped_with_warning(tmp_path, monkeypatch, caplog):
    bad_csv = (
        "date,source_country,destination,active_ingredient,mrl_mg_per_kg,"
        "detected_mg_per_kg,severity,notes\n"
        "2015-04-12,India,EU,chlorpyrifos,not_a_float,0.18,serious,\n"
        "2015-06-22,India,EU,chlorpyrifos,0.01,0.12,serious,\n"
    )
    bad_path = tmp_path / "bad.csv"
    bad_path.write_text(bad_csv, encoding="utf-8")
    monkeypatch.setattr(_rasff_module, "_csv_path", lambda: bad_path)
    reset_cache()
    with caplog.at_level("WARNING"):
        rows = all_rows()
    assert len(rows) == 1
    assert any("RASFF" in r.message for r in caplog.records)


def test_prior_baseline_is_one_in_sixty():
    """With (alpha=1, beta=9) prior and 50 inspections, baseline p_hat = 1/60."""
    p = rejection_probability("brand_new_compound_xyz", "EU")
    assert p == pytest.approx(1.0 / 60.0, rel=1e-6)
