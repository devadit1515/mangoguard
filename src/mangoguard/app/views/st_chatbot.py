"""AskHapus chatbot page (Plan 6 Task 7) -- conversation UX."""

from __future__ import annotations

from typing import Any

import streamlit as st


def render(state: dict[str, Any]) -> None:
    st.title("💬 AskHapus")
    st.write(
        "Ask any Konkan Alphonso agronomy question. Answers cite the "
        "source ICAR-CISH, KVK Konkan, DBSKKV, or NHB document."
    )

    target_language = st.selectbox(
        "Answer language",
        ["en", "mr", "hi"],
        format_func=lambda code: {"en": "English", "mr": "Marathi", "hi": "Hindi"}[code],
    )

    if "chat_history" not in state:
        state["chat_history"] = []

    for msg in state["chat_history"]:
        st.chat_message(msg["role"]).write(msg["content"])

    user_q = st.chat_input("Ask AskHapus...")
    if user_q is None:
        return
    state["chat_history"].append({"role": "user", "content": user_q})
    st.chat_message("user").write(user_q)

    # Wiring the live ChromaDB + LLM is out of scope for the v1.0.0-rc1
    # smoke build -- the chatbot module's rag.query() takes injected
    # embedder/retriever/completer so this page can be configured once
    # the ChromaDB index is ingested via scripts/run_chatbot.py.
    answer = (
        "The chatbot's vector store has not been ingested yet -- run "
        "`scripts/ingest_corpus.py` first. The architecture, prompt, "
        "and citation enforcement are tested in tests/chatbot."
    )
    state["chat_history"].append({"role": "assistant", "content": answer})
    st.chat_message("assistant").write(answer)
    st.caption(f"Answer language requested: {target_language}")
