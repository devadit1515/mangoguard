"""Pesticide metadata loader.

Wraps ``data/pesticide_metadata.yaml`` -- residue half-life (days),
per-acre cost (INR), and per-pathogen efficacy in [0,1] for every
active ingredient the recommender (Plan 4 Task 12) may rank.

The ranker (Plan 4 Task 11) scores candidates with::

    log_score = log(efficacy + 1e-6) - log(half_life + 1) - log(cost + 1)

Every entry in this YAML MUST also appear in
``cibrc_mango_registered.csv`` -- the registry is the source of truth
for what may be sprayed; this file just attaches numeric attributes to
each registered AI.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[3]
_METADATA_YAML = _REPO_ROOT / "data" / "pesticide_metadata.yaml"


@dataclass(frozen=True, slots=True)
class PesticideMetadata:
    """Numeric attributes for one active ingredient."""

    active_ingredient: str
    residue_half_life_days: float
    cost_per_acre_inr: float
    efficacy_per_pathogen: dict[str, float]
    source: str

    def efficacy_against(self, pathogen: str) -> float:
        """Efficacy in [0,1] against the named pathogen (0.0 if not listed)."""
        return float(self.efficacy_per_pathogen.get(pathogen.strip().lower(), 0.0))


def _yaml_path() -> Path:
    return _METADATA_YAML


@lru_cache(maxsize=1)
def _load_entries() -> tuple[PesticideMetadata, ...]:
    path = _yaml_path()
    if not path.exists():
        msg = f"Pesticide metadata YAML not found: {path}"
        raise FileNotFoundError(msg)
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not raw or "pesticides" not in raw:
        msg = f"Malformed pesticide metadata YAML (missing 'pesticides' root): {path}"
        raise ValueError(msg)
    out: list[PesticideMetadata] = []
    for entry in raw["pesticides"]:
        out.append(
            PesticideMetadata(
                active_ingredient=str(entry["active_ingredient"]).strip().lower(),
                residue_half_life_days=float(entry["residue_half_life_days"]),
                cost_per_acre_inr=float(entry["cost_per_acre_inr"]),
                efficacy_per_pathogen={
                    str(k).strip().lower(): float(v)
                    for k, v in entry["efficacy_per_pathogen"].items()
                },
                source=str(entry.get("source", "")).strip(),
            )
        )
    return tuple(out)


def reset_cache() -> None:
    _load_entries.cache_clear()


def all_metadata() -> list[PesticideMetadata]:
    return list(_load_entries())


def lookup(active_ingredient: str) -> PesticideMetadata | None:
    """Return metadata for ``active_ingredient`` or ``None`` if missing."""
    key = active_ingredient.strip().lower()
    for entry in _load_entries():
        if entry.active_ingredient == key:
            return entry
    return None


def listed_ingredients() -> set[str]:
    return {entry.active_ingredient for entry in _load_entries()}
