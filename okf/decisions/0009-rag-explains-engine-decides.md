---
type: Decision Record
title: "0009: Document search explains; the engine decides"
description: Uploaded documents are searched to answer and cite; their content never feeds route analysis. Embeddings are stored in the main database.
tags: [decision, rag, knowledge]
status: stable
decision_status: accepted
decided_on: 2026-11-10
generated: { by: claude-code/claude, at: "2026-11-10T10:50:00+00:00" }
---

# Decision

- Documents (PDF, text, Markdown) are split into passages and embedded. Passages and vectors are stored in the main database as JSON and compared in Python.
- Embeddings use `fastembed` (`BAAI/bge-small-en-v1.5`) when installed, otherwise a simple hashed word vector. `EMBEDDER=hash` forces the fallback (used in tests).
- `search_knowledge` returns passages with document title and page. The rule engine only ever reads validated rule packs and staff decisions.

# Alternatives considered

- pgvector: better at scale, but needs Postgres for local runs and tests. Deferred until document volume requires it.

# Consequences

- Works on SQLite and Postgres with no extension.
- Search reads every passage of the organisation; fine for a few hundred passages.
- The hashed fallback matches words, not meaning.
