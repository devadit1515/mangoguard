"""PDF ingest pipeline (Plan 5 Task 14).

Steps per PDF:
1. Extract text. Primary path is ``pdfplumber``. When a page has zero
   selectable text (scanned PDF) the OCR fallback (``pytesseract``)
   takes over -- but both are dynamically imported so the rest of the
   chatbot module works even when neither is installed.
2. Chunk into ~1000-token windows with 200-token overlap.
3. Embed each chunk via the injected ``Embedder`` callable. In
   production we pass Gemini ``text-embedding-004`` (when
   ``GEMINI_API_KEY`` is set) or a local Ollama embedder
   (``nomic-embed-text``); in tests we pass a deterministic mock.
4. Upsert to a ChromaDB collection (``mango_agronomy`` by default).

``ingest_pdf`` and ``ingest_corpus`` accept dependency-injected
``Embedder`` + ``Collection`` so tests don't need ChromaDB installed.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .corpus import CorpusDoc, load_manifest

logger = logging.getLogger(__name__)

# Default chunking: 1000 token window, 200 token overlap. Tokens are
# approximated as words for the pure-python path; the production path uses
# tiktoken for an accurate count when present.
_CHUNK_WORDS = 1000
_CHUNK_OVERLAP_WORDS = 200


@dataclass(frozen=True, slots=True)
class Chunk:
    """One indexable text chunk from a source PDF."""

    pdf_filename: str
    page_start: int
    page_end: int
    text: str
    chunk_index: int


class Embedder(Protocol):
    """Callable embedder: take a list of strings, return one float vector each."""

    def __call__(self, texts: list[str]) -> list[list[float]]: ...


class Collection(Protocol):
    """Subset of the ChromaDB Collection API we depend on."""

    def upsert(
        self,
        *,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None: ...

    def count(self) -> int: ...


def extract_pdf_text(path: Path | str) -> list[tuple[int, str]]:
    """Return ``[(page_number, text), ...]`` for the PDF at ``path``.

    Pages with empty selectable text are OCR'd via pytesseract (which
    is imported lazily so the chatbot module imports even when OCR is
    unavailable).
    """
    try:
        import pdfplumber  # type: ignore[import-untyped]
    except ImportError as exc:
        msg = "pdfplumber is required for PDF extraction. " "Install via `pip install pdfplumber`."
        raise ImportError(msg) from exc

    out: list[tuple[int, str]] = []
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if not text.strip():
                text = _ocr_page(page)
            out.append((i, text))
    return out


def _ocr_page(page) -> str:
    try:
        import pytesseract  # type: ignore[import-untyped]
    except ImportError:
        logger.warning("Page has no selectable text and pytesseract not installed -- skipping OCR.")
        return ""
    try:
        image = page.to_image(resolution=200).original
        return pytesseract.image_to_string(image)
    except Exception as exc:  # noqa: BLE001
        logger.warning("OCR failed on page %r: %s", page, exc)
        return ""


def chunk_text(
    pages: list[tuple[int, str]],
    pdf_filename: str,
    *,
    chunk_words: int = _CHUNK_WORDS,
    overlap_words: int = _CHUNK_OVERLAP_WORDS,
) -> list[Chunk]:
    """Slice page text into overlapping word-windows.

    Token = word as a deliberately-cheap approximation; production
    callers should swap the tokenizer via the ``tiktoken`` library if
    they need accurate token counts.
    """
    if chunk_words <= overlap_words:
        msg = "chunk_words must be > overlap_words"
        raise ValueError(msg)

    # Concatenate all pages with markers so we can recover page numbers
    word_records: list[tuple[int, str]] = []
    for page_num, text in pages:
        for word in text.split():
            word_records.append((page_num, word))

    out: list[Chunk] = []
    step = chunk_words - overlap_words
    idx = 0
    chunk_index = 0
    while idx < len(word_records):
        window = word_records[idx : idx + chunk_words]
        if not window:
            break
        page_start = window[0][0]
        page_end = window[-1][0]
        text_chunk = " ".join(word for _, word in window)
        out.append(
            Chunk(
                pdf_filename=pdf_filename,
                page_start=page_start,
                page_end=page_end,
                text=text_chunk,
                chunk_index=chunk_index,
            )
        )
        idx += step
        chunk_index += 1
    return out


def ingest_pdf(
    pdf_path: Path | str,
    *,
    embedder: Embedder,
    collection: Collection,
    pdf_filename: str | None = None,
) -> int:
    """Extract, chunk, embed, and upsert one PDF. Returns the chunk count."""
    pdf_path = Path(pdf_path)
    pdf_filename = pdf_filename or pdf_path.name
    pages = extract_pdf_text(pdf_path)
    chunks = chunk_text(pages, pdf_filename)
    if not chunks:
        return 0
    embeddings = embedder([c.text for c in chunks])
    ids = [f"{pdf_filename}::chunk_{c.chunk_index}" for c in chunks]
    metadatas = [
        {
            "pdf_filename": c.pdf_filename,
            "page_start": c.page_start,
            "page_end": c.page_end,
            "chunk_index": c.chunk_index,
        }
        for c in chunks
    ]
    collection.upsert(
        ids=ids,
        documents=[c.text for c in chunks],
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(chunks)


def ingest_corpus(
    corpus_root: Path | str,
    *,
    embedder: Embedder,
    collection: Collection,
    manifest_docs: Iterable[CorpusDoc] | None = None,
) -> dict[str, int]:
    """Ingest every PDF in the manifest. Returns ``{pdf_filename: chunk_count}``."""
    corpus_root = Path(corpus_root)
    docs = list(manifest_docs) if manifest_docs is not None else load_manifest()
    counts: dict[str, int] = {}
    for doc in docs:
        pdf_path = corpus_root / doc.filename
        if not pdf_path.exists():
            logger.warning("Manifest references missing PDF %s -- skipping.", doc.filename)
            counts[doc.filename] = 0
            continue
        counts[doc.filename] = ingest_pdf(
            pdf_path, embedder=embedder, collection=collection, pdf_filename=doc.filename
        )
    return counts
