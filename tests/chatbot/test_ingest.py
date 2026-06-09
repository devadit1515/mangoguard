"""Tests for the PDF ingest pipeline (chunking + upsert).

PDF text-extraction is exercised via a tiny in-process fixture so the
tests don't need the real pdfplumber + tesseract installed.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from mangoguard.chatbot.ingest import Chunk, chunk_text, ingest_pdf


# Mock embedder: deterministic 4-D vector based on length.
def _mock_embedder(texts):
    return [[float(len(t)) / 1000.0, 0.1, 0.2, 0.3] for t in texts]


@dataclass
class _InMemoryCollection:
    """Captures upsert calls so tests can inspect them."""

    last_ids: list = None
    last_documents: list = None
    last_embeddings: list = None
    last_metadatas: list = None
    upsert_count: int = 0

    def upsert(self, *, ids, documents, embeddings, metadatas):
        self.last_ids = ids
        self.last_documents = documents
        self.last_embeddings = embeddings
        self.last_metadatas = metadatas
        self.upsert_count += len(ids)

    def count(self):
        return self.upsert_count


def test_chunk_text_creates_overlapping_windows():
    pages = [(1, " ".join(f"word{i}" for i in range(300)))]
    chunks = chunk_text(pages, "demo.pdf", chunk_words=100, overlap_words=20)
    assert len(chunks) >= 2
    # Each chunk should be ~100 words
    for c in chunks:
        assert isinstance(c, Chunk)
        assert len(c.text.split()) <= 100


def test_chunk_text_preserves_page_numbers():
    pages = [(1, "alpha beta gamma"), (2, "delta epsilon zeta")]
    chunks = chunk_text(pages, "demo.pdf", chunk_words=4, overlap_words=1)
    # First chunk's page_start should be 1; some chunk should reach page 2
    assert chunks[0].page_start == 1
    assert any(c.page_end == 2 for c in chunks)


def test_chunk_text_overlap_must_be_smaller_than_window():
    pages = [(1, "x y z")]
    with pytest.raises(ValueError, match="chunk_words must be > overlap_words"):
        chunk_text(pages, "demo.pdf", chunk_words=5, overlap_words=5)


def test_chunk_text_empty_pages_returns_empty():
    assert chunk_text([], "demo.pdf") == []


def test_chunk_text_short_doc_returns_one_chunk():
    pages = [(1, "alpha beta gamma delta epsilon")]
    chunks = chunk_text(pages, "demo.pdf", chunk_words=100, overlap_words=10)
    assert len(chunks) == 1
    assert chunks[0].text == "alpha beta gamma delta epsilon"


def test_ingest_pdf_upserts_chunks(tmp_path, monkeypatch):
    """End-to-end: extract is mocked, chunk + embed + upsert run for real."""
    from mangoguard.chatbot import ingest as ingest_module

    def fake_extract(path):
        return [
            (1, " ".join(f"page1_word{i}" for i in range(200))),
            (2, " ".join(f"page2_word{i}" for i in range(150))),
        ]

    monkeypatch.setattr(ingest_module, "extract_pdf_text", fake_extract)
    fake_pdf = tmp_path / "doc.pdf"
    fake_pdf.write_text("(stub)", encoding="utf-8")
    collection = _InMemoryCollection()
    n = ingest_pdf(fake_pdf, embedder=_mock_embedder, collection=collection)
    assert n >= 1
    assert collection.upsert_count == n
    # Each upserted id must be unique and follow the schema
    assert len(set(collection.last_ids)) == len(collection.last_ids)
    for cid in collection.last_ids:
        assert "::chunk_" in cid


def test_ingest_pdf_attaches_pdf_filename_metadata(tmp_path, monkeypatch):
    from mangoguard.chatbot import ingest as ingest_module

    monkeypatch.setattr(
        ingest_module,
        "extract_pdf_text",
        lambda path: [(1, "alpha beta gamma delta")],
    )
    fake_pdf = tmp_path / "test_doc.pdf"
    fake_pdf.write_text("(stub)", encoding="utf-8")
    collection = _InMemoryCollection()
    ingest_pdf(fake_pdf, embedder=_mock_embedder, collection=collection)
    for meta in collection.last_metadatas:
        assert meta["pdf_filename"] == "test_doc.pdf"
        assert meta["page_start"] >= 1
        assert "chunk_index" in meta


def test_ingest_pdf_handles_empty_extraction(tmp_path, monkeypatch):
    """If extraction returns zero text, ingest_pdf should return 0 chunks."""
    from mangoguard.chatbot import ingest as ingest_module

    monkeypatch.setattr(ingest_module, "extract_pdf_text", lambda path: [(1, "")])
    fake_pdf = tmp_path / "empty.pdf"
    fake_pdf.write_text("(stub)", encoding="utf-8")
    collection = _InMemoryCollection()
    n = ingest_pdf(fake_pdf, embedder=_mock_embedder, collection=collection)
    assert n == 0
    assert collection.upsert_count == 0
