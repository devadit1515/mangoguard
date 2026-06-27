"""RASFF historical-rejection probability analyzer.

Wraps ``data/rasff_mango_rejections.csv`` -- the historical EU RASFF
(Rapid Alert System for Food and Feed) + FDA Import Refusal + Japan
MHLW notification database for Indian mango pesticide-residue rejections.

The recommender (Plan 4 Task 12) calls
:func:`rejection_probability(active_ingredient, destination)` to
demote or exclude pesticides with a history of import refusals on the
target export destination.

CSV schema:

::

    date,source_country,destination,active_ingredient,mrl_mg_per_kg,
        detected_mg_per_kg,severity,notes

Estimator
---------
Pure-frequency rejection rates over-fit on sparse data (e.g., one bad
shipment out of one inspection -> p = 1.0). We use Bayesian Beta-prior
smoothing with hyperparameters (alpha=1, beta=9) -- i.e., the prior
assumes a 10% baseline rejection rate before any evidence:

::

    p_hat = (alpha + rejections) / (alpha + beta + total_inspections)

For the Plan-4 placeholder data we treat the CSV row count per
(ingredient, destination) as the rejection count and assume a per-
ingredient baseline of 50 inspections (PLACEHOLDER -- replace with
actual EU/FDA/Japan inspection-volume data when curating).
"""

from __future__ import annotations

import csv
import logging
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_RASFF_CSV = _REPO_ROOT / "data" / "rasff_mango_rejections.csv"

# Beta-prior hyperparameters: alpha=1 successes, beta=9 failures
# -> prior mean = alpha/(alpha+beta) = 0.10 (10% baseline rejection rate)
_PRIOR_ALPHA = 1.0
_PRIOR_BETA = 9.0

# Placeholder denominator: assumed inspection count per (ingredient, dest)
# before any rejection is observed. Replace with real volume data later.
_DEFAULT_INSPECTIONS = 50


@dataclass(frozen=True, slots=True)
class RASFFRow:
    """One RASFF rejection row."""

    date: str
    source_country: str
    destination: str
    active_ingredient: str
    mrl_mg_per_kg: float
    detected_mg_per_kg: float
    severity: str
    notes: str


def _csv_path() -> Path:
    return _RASFF_CSV


@lru_cache(maxsize=1)
def _load_rows() -> tuple[RASFFRow, ...]:
    path = _csv_path()
    if not path.exists():
        msg = f"RASFF dataset not found: {path}"
        raise FileNotFoundError(msg)
    rows: list[RASFFRow] = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            try:
                rows.append(
                    RASFFRow(
                        date=row["date"].strip(),
                        source_country=row["source_country"].strip(),
                        destination=row["destination"].strip().upper(),
                        active_ingredient=row["active_ingredient"].strip().lower(),
                        mrl_mg_per_kg=float(row["mrl_mg_per_kg"]),
                        detected_mg_per_kg=float(row["detected_mg_per_kg"]),
                        severity=row.get("severity", "").strip(),
                        notes=row.get("notes", "").strip(),
                    )
                )
            except (KeyError, ValueError) as e:
                logger.warning("RASFF: dropping malformed row %d (%s): %s", row_num, row, e)
    return tuple(rows)


def reset_cache() -> None:
    _load_rows.cache_clear()


def all_rows() -> list[RASFFRow]:
    return list(_load_rows())


def _normalize_destination(destination: str) -> str:
    return destination.strip().upper()


def rejection_count(active_ingredient: str, destination: str) -> int:
    """Raw count of historical RASFF rows for (ingredient, destination)."""
    ai_key = active_ingredient.strip().lower()
    dest_key = _normalize_destination(destination)
    return sum(
        1 for r in _load_rows() if r.active_ingredient == ai_key and r.destination == dest_key
    )


def rejection_probability(
    active_ingredient: str,
    destination: str,
    *,
    inspections: int = _DEFAULT_INSPECTIONS,
) -> float:
    """Bayesian Beta-prior-smoothed rejection rate in [0, 1].

    Formula::

        p_hat = (alpha + n_rejections) / (alpha + beta + inspections)

    With the prior (alpha=1, beta=9), an ingredient with no historical
    rejections gets a baseline p_hat = 1 / 60 ~= 0.0167 against
    inspections=50, well under any sane exclusion threshold.

    A 5-rejection ingredient against the same denominator yields
    p_hat = 6 / 60 = 0.10 -- the recommender's 0.20 export cutoff (per
    spec section 4.3.3c) starts excluding only at higher counts.
    """
    rejections = rejection_count(active_ingredient, destination)
    return (_PRIOR_ALPHA + rejections) / (_PRIOR_ALPHA + _PRIOR_BETA + inspections)


def offending_ingredients(destination: str) -> set[str]:
    """All distinct active ingredients with >=1 rejection for ``destination``."""
    dest_key = _normalize_destination(destination)
    return {r.active_ingredient for r in _load_rows() if r.destination == dest_key}


def rejection_count_by_ingredient(destination: str) -> dict[str, int]:
    """Per-ingredient rejection count for the destination, sorted desc internally."""
    dest_key = _normalize_destination(destination)
    counts: dict[str, int] = defaultdict(int)
    for r in _load_rows():
        if r.destination == dest_key:
            counts[r.active_ingredient] += 1
    return dict(counts)
