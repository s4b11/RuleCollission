---
type: Project Overview
title: RuleCollision project
description: Purpose, scope, domains, technology choices, repository layout and conventions for RuleCollision.
tags: [project, scope, stack]
status: stable
generated: { by: copilot-sdk-agent/claude, at: "2026-11-08T17:39:00+05:30" }
sources:
  - id: concept
    resource: ../details.md
    title: Project concept and MVP specification
  - id: plan
    resource: ../PLAN.md
    title: Finalized build plan
---

# Purpose

RuleCollision helps when instructions from different offices cannot all be followed in the stated order, for example two desks that each require the other's document first. It captures requirements by voice or text, checks them deterministically, and produces one of three outcomes: a confirmed route, a precise clarification request to the right office, or an explicit unresolved case with evidence.[^concept] It cannot grant exceptions; only authenticated, authorised staff can.

# Scope (as decided on 2026-11-08)

| Topic | Decision |
| --- | --- |
| Goal | Portfolio project built as a complete, general app driven by rule packs |
| Primary domain | Hospital discharge with cashless insurance (fictional, synthetic data) |
| Second domain | Corporate onboarding/offboarding (fictional) |
| Language | English only |
| Budget | Free tiers only; OpenAI is a paid fallback |
| Timeline | One-week sprint |

Source: [PLAN.md](../PLAN.md) §1.[^plan]

# Users

Applicant (patient/family or employee), desk staff, and approver (an office's authorised decision-maker). Roles are planned, not yet implemented outside the engine's decision-validation logic.

# Technology stack

| Layer | Choice | State |
| --- | --- | --- |
| Rule engine | Python 3.12+, Pydantic v2, networkx, PyYAML | Implemented |
| Backend API | FastAPI, SQLAlchemy 2, Alembic, WebSockets | Planned |
| Database | Neon Postgres (free tier) | Planned |
| File storage | Cloudflare R2 (S3-compatible, via boto3) | Planned |
| Voice | LiveKit Cloud + LiveKit Agents (Python) | Planned |
| STT | Groq Whisper `whisper-large-v3-turbo` | Planned |
| LLM | Groq `openai/gpt-oss-120b` / `openai/gpt-oss-20b`; fallback OpenAI GPT-5.4 mini / GPT-5.4 | Planned |
| TTS | Deepgram Aura and Cartesia (both, selectable) | Planned |
| Frontend | React + Vite + TypeScript, Tailwind, React Flow | Planned |
| Deploy | Docker, GitHub Actions, Cloudflare Pages, Render/Fly | Planned |

See [system architecture](/architecture/system.md).

# Repository layout

| Path | Contents | State |
| --- | --- | --- |
| `details.md` | Original concept and MVP specification | Exists |
| `PLAN.md` | Finalized build plan | Exists |
| `AGENTS.md` | Agent operating instructions | Exists |
| `okf/` | This knowledge bundle | Exists |
| `backend/app/engine/` | Rule engine: models, analyzer, loader | Implemented |
| `backend/tests/` | Golden tests for both rule packs | Implemented |
| `rulepacks/` | `hospital_discharge.yaml`, `corporate_lifecycle.yaml` | Implemented |
| `scripts/check_okf.py` | Knowledge-bundle validator | Implemented |
| `backend/app/api/`, `backend/app/storage/`, `agent/`, `frontend/` | Empty placeholders | Not started |

# Conventions

- All rule-pack and test data is fictional.
- The LLM proposes; the engine and staff decide ([decision 0001](/decisions/0001-llm-proposes-engine-decides.md)).
- Domains are rule packs, not code ([decision 0002](/decisions/0002-domain-agnostic-rule-packs.md)).
- Agent workflow: [AGENTS.md](../AGENTS.md).

[^concept]: Project concept and MVP specification
[^plan]: Finalized build plan
