---
type: Project Overview
title: RuleCollision project
description: Purpose, scope, domains, technology choices, repository layout and conventions for RuleCollision.
tags: [project, scope, stack]
status: stable
generated: { by: claude-code/claude, at: "2026-11-10T10:52:00+00:00" }
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

# Scope (as decided on 2026-11-10)

| Topic | Decision |
| --- | --- |
| Product shape | Multi-organisation platform any domain can configure ([0006](/decisions/0006-configurable-platform.md)) |
| Showcase | Fictional hospital: discharge with cashless insurance |
| Second organisation | Fictional company: onboarding and offboarding |
| Channels | Web app by QR code (voice and text) and a phone line ([0011](/decisions/0011-phone-and-identification.md)) |
| Language | English only |
| Budget | Free tiers where possible; OpenAI is a paid fallback |
| Timeline | Phased ([build phases](/development/sprint-plan.md)) |

Source: [PLAN.md](../PLAN.md) §1.[^plan]

# Users

Applicant (patient/family or employee), desk staff, approver (an office's authorised decision-maker) and administrator (configures the agent in Agent Studio). Staff roles and offices are stored per organisation and enforced by the backend and the engine.

# Technology stack

| Layer | Choice | State |
| --- | --- | --- |
| Rule engine | Python 3.12+, Pydantic v2, networkx, PyYAML | Implemented, tested |
| Backend API | FastAPI, SQLAlchemy 2, PyJWT | Implemented, tested |
| Database | SQLite locally; Neon Postgres in deployment | SQLite verified; Postgres not yet run |
| File storage | Local disk; Cloudflare R2 via boto3 when configured | Local verified; R2 not yet run |
| Knowledge search | fastembed or hashed fallback; vectors stored as JSON | Fallback verified |
| Voice agent | LiveKit Agents 1.8 (Python), one deployment | Written; not run live |
| Speech | Deepgram and Cartesia for STT and TTS ([0005](/decisions/0005-deepgram-cartesia-speech.md)) | Not run live |
| LLM | Groq `openai/gpt-oss-120b`; fallback OpenAI `gpt-5.4-mini` | Not run live |
| Web app | React 19, Vite, TypeScript, Tailwind 4, LiveKit components | Implemented; builds |
| Hosting | Modal (backend), LiveKit Cloud (agent), static host (web app) | Files written; not deployed |
| CI | GitHub Actions: pytest, OKF check, web build | Written; not yet run on GitHub |

See [system architecture](/architecture/system.md).

# Repository layout

| Path | Contents |
| --- | --- |
| `details.md`, `PLAN.md`, `README.md`, `AGENTS.md` | Concept, plan, how to run, agent instructions |
| `okf/` | This knowledge bundle |
| `backend/app/engine/` | Rule engine |
| `backend/app/{api,services,rag,tools,storage,seed}/` | Platform backend |
| `backend/tests/` | Engine golden tests and API tests |
| `backend/modal_app.py` | Modal deployment entry point |
| `agent/` | The single LiveKit agent |
| `frontend/src/{patient,ops,studio,components,lib}/` | Web app |
| `rulepacks/` | Seed rule packs for the two demo organisations |
| `scripts/check_okf.py` | Knowledge-bundle validator |

# Conventions

- All rule-pack and test data is fictional.
- The LLM proposes; the engine and staff decide ([decision 0001](/decisions/0001-llm-proposes-engine-decides.md)).
- Domains are rule packs, not code ([decision 0002](/decisions/0002-domain-agnostic-rule-packs.md)).
- Agent workflow: [AGENTS.md](../AGENTS.md).

[^concept]: Project concept and MVP specification
[^plan]: Finalized build plan
