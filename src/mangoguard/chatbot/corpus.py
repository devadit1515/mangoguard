"""Corpus manifest loader (Plan 5 Task 13).

Validates ``data/chatbot_corpus/MANIFEST.yaml`` against a pydantic
schema so the ingest pipeline only ever sees well-formed entries.

The placeholder manifest has 15 entries (5 English / 5 Marathi /
5 Hindi). Pre-CREST submission expand to >= 50.
"""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MANIFEST_PATH = _REPO_ROOT / "data" / "chatbot_corpus" / "MANIFEST.yaml"

Language = Literal["en", "mr", "hi"]


class CorpusDoc(BaseModel):
    """One PDF the chatbot indexes."""

    filename: str = Field(..., min_length=1)
    source_url: str = Field(..., min_length=1)
    publication_date: date
    license: str = Field(..., min_length=1)
    language: Language
    topics: list[str] = Field(default_factory=list)
    notes: str = ""

    @field_validator("topics")
    @classmethod
    def _at_least_one_topic(cls, v: list[str]) -> list[str]:
        if not v:
            msg = "Each corpus document must have >=1 topic"
            raise ValueError(msg)
        return v


def _manifest_path() -> Path:
    return _MANIFEST_PATH


@lru_cache(maxsize=1)
def _load_documents() -> tuple[CorpusDoc, ...]:
    path = _manifest_path()
    if not path.exists():
        msg = f"Chatbot corpus manifest not found: {path}"
        raise FileNotFoundError(msg)
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not raw or "documents" not in raw:
        msg = f"Malformed chatbot corpus manifest (missing 'documents' root): {path}"
        raise ValueError(msg)
    return tuple(CorpusDoc(**entry) for entry in raw["documents"])


def reset_cache() -> None:
    _load_documents.cache_clear()


def load_manifest() -> list[CorpusDoc]:
    return list(_load_documents())


def documents_by_language(language: Language) -> list[CorpusDoc]:
    return [d for d in _load_documents() if d.language == language]


def documents_by_topic(topic: str) -> list[CorpusDoc]:
    return [d for d in _load_documents() if topic.lower() in d.topics]


def manifest_summary() -> dict[str, int]:
    """Counts by language -- used by the chatbot acceptance test."""
    docs = _load_documents()
    return {
        "total": len(docs),
        "en": sum(1 for d in docs if d.language == "en"),
        "mr": sum(1 for d in docs if d.language == "mr"),
        "hi": sum(1 for d in docs if d.language == "hi"),
    }
