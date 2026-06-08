"""MRL (Maximum Residue Limit) tables loader.

Loads per-market MRL YAML files from ``data/mrl_tables/`` and provides
a unified lookup interface. The five tables (``eu``, ``japan``,
``codex``, ``fssai``, ``buyer_specific``) all share the schema:

::

    metadata:
      source: "..."
      url: "..."
      crop: "Mango"
      accessed: "YYYY-MM-DD"
      default_floor_mg_per_kg: 0.01

    limits:
      hexaconazole:
        mrl_mg_per_kg: 0.05
      imidacloprid:
        mrl_mg_per_kg: 0.05
      ...

Looking up an ingredient not present in a table returns ``None`` --
the caller (Plan 4 Task 12 recommender) decides whether to fall through
to the table's ``default_floor_mg_per_kg`` or to the next table in the
chain.

Tables are cached on first load to avoid repeated YAML parsing inside
the recommender's per-ingredient loop.
"""

from __future__ import annotations

import logging
from functools import cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Resolved relative to the repo root so tests + Streamlit + notebooks all
# find the YAML files without environment-specific paths.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_MRL_TABLE_DIR = _REPO_ROOT / "data" / "mrl_tables"

_KNOWN_TABLES = frozenset({"eu", "japan", "codex", "fssai", "buyer_specific"})
_DEFAULT_FLOOR_MG_PER_KG = 0.01


def _table_path(market: str) -> Path:
    return _MRL_TABLE_DIR / f"{market}.yaml"


@cache
def load_mrl_table(market: str) -> dict[str, Any]:
    """Load and cache the ``market``.yaml MRL table.

    Returns the full parsed YAML (metadata + limits). Raises
    ``FileNotFoundError`` if the table doesn't exist on disk and
    ``ValueError`` if the YAML is malformed or missing the ``limits`` key.
    """
    if market not in _KNOWN_TABLES:
        logger.warning(
            "load_mrl_table: %r is not a known MRL table; expected one of %s",
            market,
            sorted(_KNOWN_TABLES),
        )

    path = _table_path(market)
    if not path.exists():
        msg = f"MRL table not found: {path}"
        raise FileNotFoundError(msg)

    try:
        with open(path, encoding="utf-8") as f:
            payload = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        msg = f"malformed YAML in {path}: {e}"
        raise ValueError(msg) from e

    if "limits" not in payload:
        msg = f"{path} missing required top-level 'limits' key"
        raise ValueError(msg)
    if "metadata" not in payload:
        logger.warning("load_mrl_table: %s missing metadata block", path)

    return payload


def lookup_mrl(market: str, active_ingredient: str) -> float | None:
    """Return the mg/kg MRL for ``active_ingredient`` in ``market`` or None.

    Lookups are case-insensitive on the ingredient slug. Returns the
    float MRL when present, ``None`` when absent. The caller should
    interpret ``None`` as "not listed in this market" and decide
    whether to apply the table's ``default_floor_mg_per_kg`` or to
    continue down the chain.
    """
    table = load_mrl_table(market)
    limits = table.get("limits") or {}
    key = active_ingredient.strip().lower()
    entry = limits.get(key)
    if entry is None:
        return None
    return float(entry["mrl_mg_per_kg"])


def default_floor(market: str) -> float:
    """Return the table's documented ``default_floor_mg_per_kg``.

    Falls back to ``0.01`` (the regulatory detection-limit default for
    pesticide residues) if the metadata block is absent.
    """
    table = load_mrl_table(market)
    metadata = table.get("metadata") or {}
    return float(metadata.get("default_floor_mg_per_kg", _DEFAULT_FLOOR_MG_PER_KG))


def listed_ingredients(market: str) -> set[str]:
    """Return the set of active-ingredient slugs explicitly listed in ``market``."""
    table = load_mrl_table(market)
    return set((table.get("limits") or {}).keys())


def strictest_mrl(markets: list[str], active_ingredient: str) -> float | None:
    """Apply ``min(MRL_i)`` across a list of MRL tables.

    Used by the recommender (Task 12) to enforce ``MarketSegment``
    chains like ``EXPORT_EU = [eu, japan]``. Returns ``None`` if the
    ingredient is unlisted in every table.
    """
    candidates: list[float] = []
    for market in markets:
        mrl = lookup_mrl(market, active_ingredient)
        if mrl is not None:
            candidates.append(mrl)
    return min(candidates) if candidates else None


def reset_cache() -> None:
    """Drop the lru_cache. Tests use this when seeding alternative YAMLs."""
    load_mrl_table.cache_clear()
