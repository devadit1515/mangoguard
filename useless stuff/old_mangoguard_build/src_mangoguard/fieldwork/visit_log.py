"""Cooperating-farmer visit logbook (Plan 6 Task 9).

Three visits planned across the 12-week build window:

* Visit 1 (Week 1-2): farm tour + connector audit + photo dataset
  collection + historical spray-log review.
* Visit 2 (Week 7-8): recommender pilot -- show the farmer this
  season's recommendations vs his planned schedule; record his accept /
  reject / modify decisions per block.
* Visit 3 (Week 10-11): debrief + harvest-time validation -- compare
  predicted yield / price / spray-cost / residue-noncompliance against
  observed outcomes.

Each visit produces a YAML record; the CREST report Section 2 (Methods)
+ Section 8 (Results) pull from this log.
"""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

_REPO_ROOT = Path(__file__).resolve().parents[3]
_FIELDWORK_DIR = _REPO_ROOT / "data" / "fieldwork"

VisitId = Literal["visit_1", "visit_2", "visit_3"]


class SprayLogEntry(BaseModel):
    """One row in the farmer's spray log (audited during Visit 1 + 3)."""

    visit_id: VisitId
    spray_date: date
    pesticide: str = Field(..., min_length=1)
    dose: str = ""
    target_pathogen: str = ""
    block_id: str = ""
    notes: str = ""


class RecommendationFeedback(BaseModel):
    """Farmer accept/reject/modify on one recommender output (Visit 2)."""

    visit_id: VisitId
    block_id: str = Field(..., min_length=1)
    recommendation_date: date
    recommended_pesticide: str
    farmer_action: Literal["accepted", "rejected", "modified", "skipped"]
    farmer_substitute: str = ""
    farmer_reason: str = ""


class VisitRecord(BaseModel):
    """Top-level visit YAML structure."""

    visit_id: VisitId
    visit_date: date
    interviewer: str = "MangoGuard student"
    location: str = "Konkan (cooperating farm)"
    weather_summary: str = ""
    notes: str = ""
    photos_collected: int = 0
    spray_log_entries: list[SprayLogEntry] = Field(default_factory=list)
    recommendation_feedback: list[RecommendationFeedback] = Field(default_factory=list)


def _fieldwork_dir() -> Path:
    return _FIELDWORK_DIR


def visit_yaml_path(visit_id: VisitId) -> Path:
    return _fieldwork_dir() / f"{visit_id}.yaml"


@lru_cache(maxsize=8)
def load_visit(visit_id: VisitId) -> VisitRecord:
    path = visit_yaml_path(visit_id)
    if not path.exists():
        msg = (
            f"Visit YAML not found: {path}. "
            "Run a farmer visit first; templates live in data/fieldwork/."
        )
        raise FileNotFoundError(msg)
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        msg = f"Malformed visit YAML at {path} -- expected a mapping."
        raise ValueError(msg)
    return VisitRecord(**raw)


def reset_cache() -> None:
    load_visit.cache_clear()


def save_visit(record: VisitRecord) -> Path:
    """Persist a ``VisitRecord`` back to disk."""
    path = visit_yaml_path(record.visit_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = record.model_dump(mode="json")
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
    reset_cache()
    return path


def all_spray_log_entries() -> list[SprayLogEntry]:
    """All entries across the three visits (for the report's audit table)."""
    out: list[SprayLogEntry] = []
    for vid in ("visit_1", "visit_2", "visit_3"):
        try:
            record = load_visit(vid)
        except FileNotFoundError:
            continue
        out.extend(record.spray_log_entries)
    return out


def all_recommendation_feedback() -> list[RecommendationFeedback]:
    out: list[RecommendationFeedback] = []
    for vid in ("visit_1", "visit_2", "visit_3"):
        try:
            record = load_visit(vid)
        except FileNotFoundError:
            continue
        out.extend(record.recommendation_feedback)
    return out


def acceptance_rate() -> float:
    """Fraction of recommendations the farmer accepted (Visit 2). Returns 0.0
    when no feedback has been recorded yet -- a useful spec-O4 placeholder."""
    feedback = all_recommendation_feedback()
    if not feedback:
        return 0.0
    accepted = sum(1 for f in feedback if f.farmer_action == "accepted")
    return accepted / len(feedback)
