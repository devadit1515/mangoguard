"""Baseline calendar-based spray-schedule parsers.

Loads the two extension-service spray schedules MangoGuard benchmarks
itself against (Plan 4 Tasks 14 + 15):

* **ICAR-CISH** (national mango calendar)
* **KVK Konkan** (regional Konkan-tuned calendar from KVK Dapoli +
  DBSKKV pamphlets)

YAML schema::

    metadata:
      source: "..."
      region: "..."
      cultivar: "..."
    schedule:
      - phenology_stage: "flowering"
        iso_week_range: [5, 9]
        pesticide: "carbendazim"
        formulation: "50 WP"
        dose: "1 g/L"
        target: "anthracnose"
        note: "..."  # optional

These baselines are calendar-only -- they spray regardless of measured
disease pressure. That's the comparison: MangoGuard sprays only when
PPI >= 50; the calendar baselines spray on schedule. The Plan 4 Task 14
backtest then asks "did the calendar baseline waste sprays vs PPI?" and
Plan 4 Task 15 asks "did either baseline pick an RASFF-rejected AI?"
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[3]
_BASELINE_DIR = _REPO_ROOT / "data" / "baseline_schedules"

BaselineSource = Literal["icar_cish", "kvk_konkan"]

_BASELINE_FILES: dict[str, str] = {
    "icar_cish": "icar_cish.yaml",
    "kvk_konkan": "kvk_konkan.yaml",
}

_WEEK_RANGE_TUPLE_SIZE = 2


@dataclass(frozen=True, slots=True)
class ScheduleEntry:
    """One line of a baseline spray schedule."""

    phenology_stage: str
    iso_week_start: int
    iso_week_end: int
    pesticide: str
    formulation: str
    dose: str
    target: str
    note: str

    def covers_week(self, iso_week: int) -> bool:
        return self.iso_week_start <= iso_week <= self.iso_week_end


@dataclass(frozen=True, slots=True)
class BaselineSchedule:
    """Full schedule from one source."""

    source: str
    region: str
    cultivar: str
    entries: tuple[ScheduleEntry, ...]


def _yaml_path(source: BaselineSource) -> Path:
    filename = _BASELINE_FILES.get(source)
    if filename is None:
        msg = f"Unknown baseline source: {source!r}. Expected one of {list(_BASELINE_FILES)}"
        raise ValueError(msg)
    return _BASELINE_DIR / filename


@lru_cache(maxsize=4)
def load_baseline(source: BaselineSource) -> BaselineSchedule:
    """Load and cache a baseline schedule from its YAML file."""
    path = _yaml_path(source)
    if not path.exists():
        msg = f"Baseline schedule YAML not found: {path}"
        raise FileNotFoundError(msg)
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not raw or "schedule" not in raw or "metadata" not in raw:
        msg = f"Malformed baseline schedule YAML (need metadata + schedule): {path}"
        raise ValueError(msg)
    metadata = raw["metadata"]
    entries: list[ScheduleEntry] = []
    for entry in raw["schedule"]:
        week_range = entry["iso_week_range"]
        if not isinstance(week_range, list) or len(week_range) != _WEEK_RANGE_TUPLE_SIZE:
            msg = f"iso_week_range must be a 2-element list, got {week_range!r}"
            raise ValueError(msg)
        entries.append(
            ScheduleEntry(
                phenology_stage=str(entry["phenology_stage"]).strip().lower(),
                iso_week_start=int(week_range[0]),
                iso_week_end=int(week_range[1]),
                pesticide=str(entry["pesticide"]).strip().lower(),
                formulation=str(entry.get("formulation", "")).strip(),
                dose=str(entry.get("dose", "")).strip(),
                target=str(entry["target"]).strip().lower(),
                note=str(entry.get("note", "")).strip(),
            )
        )
    return BaselineSchedule(
        source=str(metadata.get("source", source)),
        region=str(metadata.get("region", "")),
        cultivar=str(metadata.get("cultivar", "")),
        entries=tuple(entries),
    )


def reset_cache() -> None:
    load_baseline.cache_clear()


def get_baseline_recommendation(
    source: BaselineSource,
    iso_week: int,
    pathogen: str,
) -> str | None:
    """Return the pesticide ``source`` recommends for ``pathogen`` in ``iso_week``.

    Returns ``None`` if no schedule entry matches (week outside calendar,
    pathogen not in this baseline's coverage, etc.).
    """
    pathogen_key = pathogen.strip().lower()
    schedule = load_baseline(source)
    for entry in schedule.entries:
        if entry.target == pathogen_key and entry.covers_week(iso_week):
            return entry.pesticide
    return None


def all_pesticides_in_schedule(source: BaselineSource) -> set[str]:
    """All distinct AIs the baseline ever recommends -- used by RASFF counterfactual."""
    schedule = load_baseline(source)
    return {entry.pesticide for entry in schedule.entries}


def schedule_for_week(
    source: BaselineSource,
    iso_week: int,
) -> list[ScheduleEntry]:
    """All entries whose week range covers ``iso_week`` -- the day's calendar action."""
    schedule = load_baseline(source)
    return [entry for entry in schedule.entries if entry.covers_week(iso_week)]
