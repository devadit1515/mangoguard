"""CIB&RC (Central Insecticides Board & Registration Committee) registry.

Wraps ``data/cibrc_mango_registered.csv`` -- the list of pesticide active
ingredients legally registered for use on mango in India. The recommender
(Plan 4 Task 12) filters all candidate spray recommendations through
``pesticides_for_pathogen()`` so that only India-registered active
ingredients are ever suggested.

CSV schema (one row per registered AI for one target pathogen class):

::

    active_ingredient,formulation,dose_per_liter_water,target_pest_class,
        phi_days,registration_status,notes

Pre-CREST-submission the placeholder rows in the CSV must be refreshed
against the live CIB&RC mango registration list
(https://cibrc.nic.in/).
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CIBRC_CSV = _REPO_ROOT / "data" / "cibrc_mango_registered.csv"


@dataclass(frozen=True, slots=True)
class CIBRCEntry:
    """One CIB&RC-registered (active_ingredient, target_pathogen) row."""

    active_ingredient: str
    formulation: str
    dose_per_liter_water: str
    target_pest_class: str
    phi_days: int
    registration_status: str
    notes: str


def _csv_path() -> Path:
    return _CIBRC_CSV


@lru_cache(maxsize=1)
def _load_entries() -> tuple[CIBRCEntry, ...]:
    """Read + cache the CSV. Cached because the recommender hits it once per call."""
    path = _csv_path()
    if not path.exists():
        msg = f"CIB&RC registry not found: {path}"
        raise FileNotFoundError(msg)
    entries: list[CIBRCEntry] = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            try:
                entries.append(
                    CIBRCEntry(
                        active_ingredient=row["active_ingredient"].strip().lower(),
                        formulation=row["formulation"].strip(),
                        dose_per_liter_water=row["dose_per_liter_water"].strip(),
                        target_pest_class=row["target_pest_class"].strip().lower(),
                        phi_days=int(row["phi_days"]),
                        registration_status=row.get("registration_status", "").strip(),
                        notes=row.get("notes", "").strip(),
                    )
                )
            except (KeyError, ValueError) as e:
                logger.warning("CIB&RC: dropping malformed row %d (%s): %s", row_num, row, e)
    return tuple(entries)


def reset_cache() -> None:
    """Drop the lru_cache. Tests use this when seeding an alternative CSV."""
    _load_entries.cache_clear()


def all_entries() -> list[CIBRCEntry]:
    """Return every registered (AI, pathogen) row."""
    return list(_load_entries())


def pesticides_for_pathogen(pathogen: str) -> list[CIBRCEntry]:
    """All CIB&RC-registered active ingredients targeting ``pathogen``.

    Pathogen names are case-insensitive. Returns an empty list when the
    pathogen has no registered AIs (the recommender will return a
    no-spray recommendation with an explanatory rationale).
    """
    pathogen_key = pathogen.strip().lower()
    return [e for e in _load_entries() if e.target_pest_class == pathogen_key]


def get_phi_days(active_ingredient: str) -> int | None:
    """Return the minimum PHI for an active ingredient across all its registrations.

    An ingredient may be registered for multiple pathogens with different
    PHIs; the recommender uses the conservative (highest) value, but
    callers asking "what's the absolute earliest I can harvest" want the
    minimum. We expose the min here and let recommenders use ``max()``
    via :func:`max_phi_days` when stricter.
    """
    key = active_ingredient.strip().lower()
    phis = [e.phi_days for e in _load_entries() if e.active_ingredient == key]
    return min(phis) if phis else None


def max_phi_days(active_ingredient: str) -> int | None:
    """Return the conservative (highest) PHI across all registrations."""
    key = active_ingredient.strip().lower()
    phis = [e.phi_days for e in _load_entries() if e.active_ingredient == key]
    return max(phis) if phis else None


def is_registered(active_ingredient: str) -> bool:
    key = active_ingredient.strip().lower()
    return any(e.active_ingredient == key for e in _load_entries())


def registered_ingredients() -> set[str]:
    return {e.active_ingredient for e in _load_entries()}
