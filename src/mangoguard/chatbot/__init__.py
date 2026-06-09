"""Module 5 -- AskHapus RAG chatbot.

Pipeline:
1. ``corpus`` -- manifest of agronomy PDFs (ICAR-CISH, KVK Konkan,
   DBSKKV Dapoli, NHB handbook, FAO production manual).
2. ``ingest`` -- PDF text extraction (pdfplumber + OCR fallback),
   chunk + overlap, embed (Gemini text-embedding-004 OR local Ollama),
   upsert to ChromaDB.
3. ``rag`` -- retrieve top-k chunks, call LLM with citation-enforced
   system prompt, return cited answer.

LLM dependencies are mockable; tests run without network access by
injecting a callable for the embedder + completer.
"""
