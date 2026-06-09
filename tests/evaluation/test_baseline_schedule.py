"""Tests for the ICAR-CISH + KVK Konkan baseline schedule parsers."""

from __future__ import annotations

import pytest

from mangoguard.evaluation import baseline_schedule as _module
from mangoguard.evaluation.baseline_schedule import (
    BaselineSchedule,
    ScheduleEntry,
    all_pesticides_in_schedule,
    get_baseline_recommendation,
    load_baseline,
    reset_cache,
    schedule_for_week,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    reset_cache()
    yield
    reset_cache()


def test_loads_icar_cish_yaml():
    schedule = load_baseline("icar_cish")
    assert isinstance(schedule, BaselineSchedule)
    assert "ICAR-CISH" in schedule.source
    assert "Konkan" in schedule.region or "Western" in schedule.region
    assert "Alphonso" in schedule.cultivar
    assert len(schedule.entries) >= 5


def test_loads_kvk_konkan_yaml():
    schedule = load_baseline("kvk_konkan")
    assert isinstance(schedule, BaselineSchedule)
    assert "KVK" in schedule.source or "Konkan" in schedule.source
    assert len(schedule.entries) >= 5


def test_every_entry_has_valid_week_range():
    for source in ("icar_cish", "kvk_konkan"):
        schedule = load_baseline(source)
        for entry in schedule.entries:
            assert isinstance(entry, ScheduleEntry)
            assert 1 <= entry.iso_week_start <= 53
            assert entry.iso_week_start <= entry.iso_week_end <= 53
            assert entry.pesticide
            assert entry.target


def test_pesticides_normalized_to_lowercase():
    for source in ("icar_cish", "kvk_konkan"):
        for entry in load_baseline(source).entries:
            assert entry.pesticide == entry.pesticide.lower()
            assert entry.target == entry.target.lower()


def test_returns_pesticide_for_known_week_pathogen():
    """ICAR-CISH ISO week 7 (flowering) should recommend carbendazim for anthracnose."""
    result = get_baseline_recommendation("icar_cish", iso_week=7, pathogen="anthracnose")
    assert result is not None
    assert isinstance(result, str)


def test_returns_none_outside_schedule_window():
    """Week 50 (post-harvest dormancy) is not covered -- no schedule entry."""
    result = get_baseline_recommendation("icar_cish", iso_week=50, pathogen="anthracnose")
    assert result is None


def test_returns_none_for_pathogen_not_in_baseline():
    result = get_baseline_recommendation("icar_cish", iso_week=7, pathogen="dragon_pox")
    assert result is None


def test_pathogen_lookup_case_insensitive():
    a = get_baseline_recommendation("icar_cish", iso_week=7, pathogen="ANTHRACNOSE")
    b = get_baseline_recommendation("icar_cish", iso_week=7, pathogen="anthracnose")
    assert a == b


def test_kvk_konkan_includes_neem_oil_organic_option():
    """KVK Konkan baseline contains an organic neem_oil hopper intervention."""
    pesticides = all_pesticides_in_schedule("kvk_konkan")
    assert "neem_oil" in pesticides


def test_icar_cish_does_not_include_konkan_specific_addons():
    """ICAR-CISH is the national calendar -- shouldn't have the KVK-only neem hopper round."""
    cish_week_3 = get_baseline_recommendation("icar_cish", iso_week=3, pathogen="hopper")
    kvk_week_3 = get_baseline_recommendation("kvk_konkan", iso_week=3, pathogen="hopper")
    # KVK has a week-3 pre-flowering hopper spray; CISH does not
    assert kvk_week_3 == "neem_oil"
    assert cish_week_3 is None


def test_schedule_for_week_returns_all_matching_entries():
    """ISO week 7 should pull both anthracnose + powdery_mildew sprays in flowering window."""
    entries = schedule_for_week("icar_cish", iso_week=7)
    assert len(entries) >= 2
    targets = {entry.target for entry in entries}
    assert "anthracnose" in targets
    assert "powdery_mildew" in targets


def test_schedule_for_week_outside_range_empty():
    entries = schedule_for_week("icar_cish", iso_week=52)
    assert entries == []


def test_unknown_source_raises():
    with pytest.raises(ValueError, match="Unknown baseline source"):
        load_baseline("bogus_source")  # type: ignore[arg-type]


def test_missing_yaml_raises(tmp_path, monkeypatch):
    fake_dir = tmp_path / "no_such_dir"
    monkeypatch.setattr(_module, "_BASELINE_DIR", fake_dir)
    reset_cache()
    with pytest.raises(FileNotFoundError, match="Baseline schedule YAML not found"):
        load_baseline("icar_cish")


def test_malformed_yaml_raises(tmp_path, monkeypatch):
    bad_dir = tmp_path / "bad"
    bad_dir.mkdir()
    (bad_dir / "icar_cish.yaml").write_text("just_a_string\n", encoding="utf-8")
    monkeypatch.setattr(_module, "_BASELINE_DIR", bad_dir)
    reset_cache()
    with pytest.raises(ValueError, match="Malformed baseline schedule YAML"):
        load_baseline("icar_cish")


def test_all_pesticides_in_schedule_returns_set():
    pesticides = all_pesticides_in_schedule("icar_cish")
    assert isinstance(pesticides, set)
    assert len(pesticides) >= 5
    for p in pesticides:
        assert p == p.lower()


def test_kvk_konkan_hopper_window_extends_past_cish():
    """KVK Konkan addresses the flowering-tail hopper peak that CISH misses."""
    # KVK has hopper coverage around weeks 9-11 (flowering tail)
    kvk_w10 = get_baseline_recommendation("kvk_konkan", iso_week=10, pathogen="hopper")
    assert kvk_w10 is not None


def test_baselines_share_pre_harvest_short_phi_protectant():
    """Both baselines end with copper_oxychloride (PHI=7d) at pre-harvest."""
    cish_w18 = get_baseline_recommendation("icar_cish", iso_week=18, pathogen="anthracnose")
    kvk_w18 = get_baseline_recommendation("kvk_konkan", iso_week=18, pathogen="anthracnose")
    assert cish_w18 == "copper_oxychloride"
    assert kvk_w18 == "copper_oxychloride"
