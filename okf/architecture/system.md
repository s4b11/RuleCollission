---
type: Architecture
title: System architecture
description: Planned components, pipeline, data model and Cloudflare R2 storage layout; only the rule engine is implemented.
tags: [architecture, planned, storage, voice]
status: draft
generated: { by: copilot-sdk-agent/claude, at: "2026-11-08T17:39:00+05:30" }
sources:
  - id: plan
    resource: ../../PLAN.md
    title: Finalized build plan
  - id: concept
    resource: ../../details.md
    title: Project concept and MVP specification
---

> **Status:** Intended design. Apart from the [rule engine](/architecture/rule-engine.md), none of the components below exist yet.[^plan]

# Components

```text
React (Vite, Tailwind, React Flow, LiveKit components)  — Cloudflare Pages
        │  REST + WebSocket                │ WebRTC
        ▼                                  ▼
FastAPI backend  ◄──── tool calls ────  LiveKit Agent worker (Python)
  │  auth (JWT roles)                    STT: Groq Whisper
  │  cases / evidence / reviews          LLM: Groq gpt-oss → OpenAI fallback
  │  rule engine (deterministic)         TTS: Deepgram Aura / Cartesia
  ├── Neon Postgres (metadata, versions, decisions, audit)
  └── Cloudflare R2 (evidence, consented recordings, report PDFs)
```

# Pipeline

1. Voice or text intake → STT.
2. LLM extraction proposes requirements through the `propose_requirement` tool.
3. Readback and confirmation of names, dates, negations and either/both conditions.
4. Requirement store (unverified until confirmed by the issuing office).
5. [Rule engine](/architecture/rule-engine.md) analysis → route, blocking groups, clarifications.
6. Staff review: authenticated, case-scoped decisions.
7. Recompute. Route states: suggested → confirmed → completed, or unresolved.

Invariant: [the LLM proposes; the engine and staff decide](/decisions/0001-llm-proposes-engine-decides.md).

# Storage (Cloudflare R2)

Decided in [decision 0003](/decisions/0003-cloudflare-r2-storage.md).

| Prefix | Contents |
| --- | --- |
| `evidence/{case_id}/` | Discharge summaries, pre-authorisation letters, TPA queries, bills, photos of written instructions |
| `recordings/{case_id}/` | Session audio, only with consent |
| `reports/{case_id}/` | Generated route-summary and unresolved-case PDFs |

Browser uploads use presigned PUT URLs; downloads use short-lived presigned GET URLs. Postgres stores only key, SHA-256, size, MIME type and verification status.

# Planned data model

`Case`, `Requirement` (versioned, append-only), `Evidence`, `Authority`, `Decision`, `Route`, `Clarification`, `AuditEvent`. Uncertainty is tracked as three separate fields: transcription, interpretation and authority verification.[^concept] The engine already defines in-memory Pydantic equivalents for several of these in `backend/app/engine/models.py`.

# Planned agent tools

`get_case_context`, `lookup_approved_rules`, `propose_requirement`, `confirm_requirement`, `analyze_routes`, `prepare_clarification`, `request_staff_review` (idempotency key), `build_route_summary`.

# Security notes (planned)

- JWT roles: `applicant`, `desk_staff`, `approver`, scoped by office.
- Uploaded text is evidence, never instructions to the model.
- Provider keys only in an uncommitted `.env`.

[^plan]: Finalized build plan
[^concept]: Project concept and MVP specification
