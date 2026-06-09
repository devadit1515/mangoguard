"""Tests for the RAG query module."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from mangoguard.chatbot.rag import ChatbotResponse, Citation, query


def _mock_embedder(texts):
    return [[0.1, 0.2, 0.3, 0.4] for _ in texts]


@dataclass
class _MockRetriever:
    """Returns canned chunks for query() calls."""

    documents: list[str] = field(default_factory=list)
    metadatas: list[dict] = field(default_factory=list)

    def query(self, *, query_embeddings, n_results):
        return {
            "documents": [self.documents[:n_results]],
            "metadatas": [self.metadatas[:n_results]],
            "ids": [[f"id{i}" for i in range(min(n_results, len(self.documents)))]],
        }


def _canned_completer(answer: str):
    def fn(system_prompt: str, user_question: str) -> str:
        return answer

    return fn


def test_query_returns_chatbot_response():
    retriever = _MockRetriever(
        documents=["Anthracnose is caused by Colletotrichum gloeosporioides."],
        metadatas=[{"pdf_filename": "icar_cish_mango_ipm.pdf", "page_start": 12}],
    )
    response = query(
        "What causes anthracnose?",
        embedder=_mock_embedder,
        retriever=retriever,
        completer=_canned_completer(
            "Caused by Colletotrichum [source: icar_cish_mango_ipm.pdf p.12]"
        ),
    )
    assert isinstance(response, ChatbotResponse)


def test_response_includes_citations():
    retriever = _MockRetriever(
        documents=["Spray hexaconazole 2 ml/L at flowering."],
        metadatas=[{"pdf_filename": "kvk_dapoli_alphonso_calendar.pdf", "page_start": 5}],
    )
    response = query(
        "When to spray hexaconazole?",
        embedder=_mock_embedder,
        retriever=retriever,
        completer=_canned_completer(
            "At flowering, 2 ml/L [source: kvk_dapoli_alphonso_calendar.pdf p.5]"
        ),
    )
    assert len(response.citations) == 1
    citation = response.citations[0]
    assert isinstance(citation, Citation)
    assert citation.pdf == "kvk_dapoli_alphonso_calendar.pdf"
    assert citation.page == 5


def test_refuses_to_answer_without_context():
    """When the retriever returns zero chunks, the response must be the refusal."""
    retriever = _MockRetriever(documents=[], metadatas=[])
    response = query(
        "What is the capital of France?",
        embedder=_mock_embedder,
        retriever=retriever,
        completer=_canned_completer("Paris"),
    )
    assert response.citations == []
    assert "KVK extension officer" in response.answer


def test_target_language_marathi_routes_through():
    retriever = _MockRetriever(
        documents=["English source text"],
        metadatas=[{"pdf_filename": "doc.pdf", "page_start": 1}],
    )
    response = query(
        "anthracnose kashi tholavayachi",
        embedder=_mock_embedder,
        retriever=retriever,
        completer=_canned_completer("Anthracnose nivaranasathi..."),
        target_language="mr",
    )
    assert response.language == "mr"


def test_target_language_hindi_routes_through():
    retriever = _MockRetriever(
        documents=["Hopper management text"],
        metadatas=[{"pdf_filename": "doc.pdf", "page_start": 3}],
    )
    response = query(
        "Mango hopper kaise rokein?",
        embedder=_mock_embedder,
        retriever=retriever,
        completer=_canned_completer("Hopper ke liye..."),
        target_language="hi",
    )
    assert response.language == "hi"


def test_unknown_target_language_raises():
    retriever = _MockRetriever()
    with pytest.raises(ValueError, match="target_language must be"):
        query(
            "test",
            embedder=_mock_embedder,
            retriever=retriever,
            completer=_canned_completer("x"),
            target_language="fr",
        )


def test_top_k_caps_retrieval():
    retriever = _MockRetriever(
        documents=[f"chunk {i}" for i in range(10)],
        metadatas=[{"pdf_filename": f"doc_{i}.pdf", "page_start": i} for i in range(10)],
    )
    response = query(
        "test",
        embedder=_mock_embedder,
        retriever=retriever,
        completer=_canned_completer("answer"),
        k=3,
    )
    assert len(response.citations) == 3


def test_citation_pdf_and_page_extracted_from_metadata():
    retriever = _MockRetriever(
        documents=["source A", "source B"],
        metadatas=[
            {"pdf_filename": "alpha.pdf", "page_start": 7},
            {"pdf_filename": "beta.pdf", "page_start": 15},
        ],
    )
    response = query(
        "test",
        embedder=_mock_embedder,
        retriever=retriever,
        completer=_canned_completer("answer"),
        k=2,
    )
    pdfs = {c.pdf for c in response.citations}
    assert pdfs == {"alpha.pdf", "beta.pdf"}
