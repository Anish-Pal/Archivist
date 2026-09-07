---
title: Archivist
emoji: 📚
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Enterprise RAG assistant with hybrid retrieval and citations
---

# Archivist — Enterprise RAG Assistant

Upload PDF, TXT, and CSV documents and ask questions about them in plain
language. Answers are grounded in retrieved passages and carry citations that
trace back to the source document.

Retrieval combines dense vector search (ChromaDB, `BAAI/bge-small-en-v1.5`)
with BM25 keyword search, fuses the two with Reciprocal Rank Fusion, and
reranks the candidates with `BAAI/bge-reranker-base` before the context reaches
the LLM. Every account sees only its own documents.

Source: https://github.com/Anish-Pal/Archivist

## Runtime configuration

Set these under **Settings → Variables and secrets**:

| Secret | Purpose |
|---|---|
| `DB_URL` | PostgreSQL connection string (Neon, with `?sslmode=require`) |
| `GROQ_API_KEY` | Groq API key used for answer generation and query rewriting |

Persistent storage mounted at `/data` holds uploaded files and the Chroma
index. Without it the Space still runs, but both are cleared on every restart.
