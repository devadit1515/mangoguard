"""RAG query with citation enforcement (Plan 5 Task 15).

The user asks a question -> we embed it, retrieve top-K chunks from the
ChromaDB collection, build a system prompt that REQUIRES the LLM to
cite the source PDF + page for every factual claim, and call the LLM.

Both the embedder and the completer are injected so tests run without
network access; the production wiring (Gemini 1.5 Flash + fallback
Ollama Llama-3-8B) sits in ``scripts/run_chatbot.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

_DEFAULT_K = 5
_SYSTEM_PROMPT_TEMPLATE = """\
You are AskHapus, an expert assistant for Konkan Alphonso mango growers.

You MUST follow these rules:
1. Answer ONLY using the provided context. If the context does not contain
   the information, reply: "I do not have a verified source for that. Please
   ask your local KVK extension officer."
2. Cite the source PDF and page number for every factual claim. Citation
   format: [source: <pdf_filename> p.<page>]
3. Write the answer in {target_language}.
4. Keep the answer under 200 words for simple questions; use bullet points
   for multi-step instructions.

Context:
{context}
"""


class Embedder(Protocol):
    """Same protocol as ``ingest.Embedder`` -- repeat here so this module's
    public API is self-contained."""

    def __call__(self, texts: list[str]) -> list[list[float]]: ...


class Completer(Protocol):
    """LLM completion callable -- (system_prompt, user_question) -> answer."""

    def __call__(self, system_prompt: str, user_question: str) -> str: ...


class Retriever(Protocol):
    """ChromaDB Collection.query subset."""

    def query(
        self,
        *,
        query_embeddings: list[list[float]],
        n_results: int,
    ) -> dict: ...


@dataclass(frozen=True, slots=True)
class Citation:
    """One PDF + page citation surfaced in the answer."""

    pdf: str
    page: int
    snippet: str


@dataclass(frozen=True, slots=True)
class ChatbotResponse:
    """Outcome of a ``query`` call."""

    answer: str
    citations: list[Citation] = field(default_factory=list)
    language: str = "en"


_LANGUAGE_NAMES = {"en": "English", "mr": "Marathi", "hi": "Hindi"}


def _build_context_block(retrieved: dict) -> tuple[str, list[Citation]]:
    """Render the retrieved chunks into the system prompt's context block
    and collect citations.

    ChromaDB query returns
    ``{ids: [[id1, id2, ...]], documents: [[d1, d2, ...]],
       metadatas: [[m1, m2, ...]]}`` where the outer list is per-query.
    """
    docs = retrieved.get("documents", [[]])[0]
    metas = retrieved.get("metadatas", [[]])[0]
    blocks: list[str] = []
    citations: list[Citation] = []
    for doc_text, meta in zip(docs, metas, strict=True):
        pdf = str(meta.get("pdf_filename", "unknown.pdf"))
        page_start = int(meta.get("page_start", 0))
        snippet = doc_text[:200] + ("..." if len(doc_text) > 200 else "")  # noqa: PLR2004
        blocks.append(f"[source: {pdf} p.{page_start}]\n{doc_text}")
        citations.append(Citation(pdf=pdf, page=page_start, snippet=snippet))
    return "\n\n".join(blocks), citations


def query(
    question: str,
    *,
    embedder: Embedder,
    retriever: Retriever,
    completer: Completer,
    target_language: str = "en",
    k: int = _DEFAULT_K,
) -> ChatbotResponse:
    """End-to-end RAG query.

    Args:
        question: User question.
        embedder: Same embedder used at ingest time.
        retriever: A ChromaDB collection (or any object with the
            matching ``query`` method).
        completer: An LLM completer callable.
        target_language: ``"en"`` / ``"mr"`` / ``"hi"``. The system prompt
            forces the answer language.
        k: Number of chunks to retrieve.

    Returns:
        ``ChatbotResponse`` with answer, citations, and language.
    """
    if target_language not in _LANGUAGE_NAMES:
        msg = f"target_language must be one of {list(_LANGUAGE_NAMES)}, got {target_language!r}"
        raise ValueError(msg)

    query_embedding = embedder([question])
    retrieved = retriever.query(query_embeddings=query_embedding, n_results=k)
    context_block, citations = _build_context_block(retrieved)

    if not citations:
        return ChatbotResponse(
            answer=(
                "I do not have a verified source for that. Please ask your local "
                "KVK extension officer."
            ),
            citations=[],
            language=target_language,
        )

    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        target_language=_LANGUAGE_NAMES[target_language],
        context=context_block,
    )
    answer = completer(system_prompt, question)
    return ChatbotResponse(
        answer=answer,
        citations=citations,
        language=target_language,
    )
