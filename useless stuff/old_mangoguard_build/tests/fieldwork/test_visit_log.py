"""Tests for the cooperating-farmer visit logbook."""

from __future__ import annotations

from datetime import date

import pytest

from mangoguard.fieldwork import visit_log as _visit_module
from mangoguard.fieldwork.visit_log import (
    RecommendationFeedback,
    SprayLogEntry,
    VisitRecord,
    acceptance_rate,
    all_recommendation_feedback,
    all_spray_log_entries,
    load_visit,
    reset_cache,
    save_visit,
    visit_yaml_path,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    reset_cache()
    yield
    reset_cache()


def test_visit_1_template_loads():
    record = load_visit("visit_1")
    assert isinstance(record, VisitRecord)
    assert record.visit_id == "visit_1"


def test_all_three_visit_templates_loadable():
    for vid in ("visit_1", "visit_2", "visit_3"):
        record = load_visit(vid)
        assert record.visit_id == vid


def test_load_visit_unknown_file_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(_visit_module, "_fieldwork_dir", lambda: tmp_path)
    reset_cache()
    with pytest.raises(FileNotFoundError, match="Visit YAML not found"):
        load_visit("visit_1")


def test_save_visit_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(_visit_module, "_fieldwork_dir", lambda: tmp_path)
    reset_cache()
    record = VisitRecord(
        visit_id="visit_1",
        visit_date=date(2026, 6, 15),
        weather_summary="hot + humid",
        notes="captured 25 photos",
        photos_collected=25,
    )
    save_visit(record)
    loaded = load_visit("visit_1")
    assert loaded.weather_summary == "hot + humid"
    assert loaded.photos_collected == 25


def test_save_visit_with_spray_entries_round_trips(tmp_path, monkeypatch):
    monkeypatch.setattr(_visit_module, "_fieldwork_dir", lambda: tmp_path)
    reset_cache()
    record = VisitRecord(
        visit_id="visit_1",
        visit_date=date(2026, 6, 15),
        spray_log_entries=[
            SprayLogEntry(
                visit_id="visit_1",
                spray_date=date(2026, 5, 1),
                pesticide="hexaconazole",
                dose="2 ml/L",
                target_pathogen="anthracnose",
                block_id="block_A",
                notes="pre-flowering",
            )
        ],
    )
    save_visit(record)
    loaded = load_visit("visit_1")
    assert len(loaded.spray_log_entries) == 1
    assert loaded.spray_log_entries[0].pesticide == "hexaconazole"


def test_save_visit_with_recommendation_feedback_round_trips(tmp_path, monkeypatch):
    monkeypatch.setattr(_visit_module, "_fieldwork_dir", lambda: tmp_path)
    reset_cache()
    record = VisitRecord(
        visit_id="visit_2",
        visit_date=date(2026, 7, 25),
        recommendation_feedback=[
            RecommendationFeedback(
                visit_id="visit_2",
                block_id="block_A",
                recommendation_date=date(2026, 7, 20),
                recommended_pesticide="hexaconazole",
                farmer_action="accepted",
            )
        ],
    )
    save_visit(record)
    loaded = load_visit("visit_2")
    assert loaded.recommendation_feedback[0].farmer_action == "accepted"


def test_all_spray_log_entries_returns_list():
    entries = all_spray_log_entries()
    assert isinstance(entries, list)
    # Templates start empty
    assert all(isinstance(e, SprayLogEntry) for e in entries)


def test_all_recommendation_feedback_returns_list():
    feedback = all_recommendation_feedback()
    assert isinstance(feedback, list)


def test_acceptance_rate_empty_returns_zero():
    """With no feedback recorded, acceptance rate is 0 (spec-O4 placeholder)."""
    assert acceptance_rate() == 0.0


def test_visit_yaml_path_returns_per_visit_filename():
    p1 = visit_yaml_path("visit_1")
    p2 = visit_yaml_path("visit_2")
    p3 = visit_yaml_path("visit_3")
    assert p1.name == "visit_1.yaml"
    assert p2.name == "visit_2.yaml"
    assert p3.name == "visit_3.yaml"


def test_acceptance_rate_computes_from_recorded_feedback(tmp_path, monkeypatch):
    monkeypatch.setattr(_visit_module, "_fieldwork_dir", lambda: tmp_path)
    reset_cache()
    record = VisitRecord(
        visit_id="visit_2",
        visit_date=date(2026, 7, 25),
        recommendation_feedback=[
            RecommendationFeedback(
                visit_id="visit_2",
                block_id="block_A",
                recommendation_date=date(2026, 7, 20),
                recommended_pesticide="hexaconazole",
                farmer_action="accepted",
            ),
            RecommendationFeedback(
                visit_id="visit_2",
                block_id="block_B",
                recommendation_date=date(2026, 7, 20),
                recommended_pesticide="mancozeb",
                farmer_action="rejected",
                farmer_reason="cost concern",
            ),
        ],
    )
    save_visit(record)
    rate = acceptance_rate()
    assert rate == 0.5
