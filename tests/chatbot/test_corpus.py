"""Tests for the chatbot corpus manifest loader."""

from __future__ import annotations

import pytest

from mangoguard.chatbot import corpus as _corpus_module
from mangoguard.chatbot.corpus import (
    CorpusDoc,
    documents_by_language,
    documents_by_topic,
    load_manifest,
    manifest_summary,
    reset_cache,
)


@pytest.fixture(autouse=True)
def _clear_cache():
    reset_cache()
    yield
    reset_cache()


def test_manifest_yaml_loads():
    docs = load_manifest()
    assert len(docs) >= 15


def test_every_entry_has_required_fields():
    for doc in load_manifest():
        assert isinstance(doc, CorpusDoc)
        assert doc.filename
        assert doc.source_url
        assert doc.publication_date is not None
        assert doc.license
        assert doc.language in ("en", "mr", "hi")
        assert len(doc.topics) >= 1


def test_at_least_5_english_sources():
    en = documents_by_language("en")
    assert len(en) >= 5


def test_at_least_5_marathi_sources():
    mr = documents_by_language("mr")
    assert len(mr) >= 5


def test_at_least_5_hindi_sources():
    hi = documents_by_language("hi")
    assert len(hi) >= 5


def test_documents_by_topic_filters_correctly():
    """At least one entry covers 'anthracnose'."""
    docs = documents_by_topic("anthracnose")
    assert len(docs) >= 1
    for d in docs:
        assert "anthracnose" in d.topics


def test_documents_by_topic_is_case_insensitive():
    a = documents_by_topic("anthracnose")
    b = documents_by_topic("ANTHRACNOSE")
    assert {d.filename for d in a} == {d.filename for d in b}


def test_manifest_summary_returns_counts():
    summary = manifest_summary()
    assert summary["total"] == summary["en"] + summary["mr"] + summary["hi"]


def test_missing_manifest_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(_corpus_module, "_manifest_path", lambda: tmp_path / "no_such.yaml")
    reset_cache()
    with pytest.raises(FileNotFoundError, match="Chatbot corpus manifest not found"):
        load_manifest()


def test_malformed_manifest_raises(tmp_path, monkeypatch):
    bad = tmp_path / "bad.yaml"
    bad.write_text("not_documents_root: []\n", encoding="utf-8")
    monkeypatch.setattr(_corpus_module, "_manifest_path", lambda: bad)
    reset_cache()
    with pytest.raises(ValueError, match="Malformed chatbot corpus manifest"):
        load_manifest()


def test_entry_with_empty_topics_rejected(tmp_path, monkeypatch):
    bad_yaml = """
documents:
  - filename: bad.pdf
    source_url: https://example.com/bad.pdf
    publication_date: '2024-01-01'
    license: cc_by
    language: en
    topics: []
"""
    bad = tmp_path / "bad.yaml"
    bad.write_text(bad_yaml, encoding="utf-8")
    monkeypatch.setattr(_corpus_module, "_manifest_path", lambda: bad)
    reset_cache()
    with pytest.raises(Exception):  # noqa: B017,PT011 -- pydantic re-raises -> ValidationError chain
        load_manifest()
