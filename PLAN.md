# RuleCollision — Build Plan (Finalized)

> Voice + text agent that detects incompatible administrative requirements across offices and produces a confirmed route, a targeted clarification, or an evidence-backed unresolved report.

See [details.md](./details.md) for the full concept.

## 1. Decisions

| Topic | Decision |
| --- | --- |
| Goal | Portfolio project built as a complete, general "rule pack" app |
| Primary domain | Hospital discharge + cashless insurance (fictional hospital/insurer/TPA, synthetic data) |
| Second domain | Corporate onboarding/offboarding (HR ↔ IT ↔ Finance ↔ Admin) |
| Language | English only |
| Budget | Free tiers only (OpenAI used only as paid fallback) |
| LLM | Groq `openai/gpt-oss-120b` (extraction/tools), `openai/gpt-oss-20b` (readback/summaries); fallback OpenAI `gpt-5.4-mini` → `gpt-5.4` |
| STT | Groq Whisper `whisper-large-v3-turbo` |
| TTS | Deepgram Aura (primary) + Cartesia (alternate/fallback), selectable per session |
| Storage | Cloudflare R2 (S3-compatible) |
| Timeline | 1-week sprint |

## 2. Domains as rule packs

The engine is domain-agnostic. Each domain is a YAML **rule pack** under `rulepacks/`:

- `offices` — desks/departments and who has decision authority
- `documents` — canonical document IDs + known aliases
- `requirements` — `office` + `action` + prerequisite expression (`all_of` / `any_of` / nested) + applicability + effective dates
- `alternatives` — approved alternatives (e.g., provisional documents) and who must accept them

### 2.1 Hospital discharge + insurance (primary)

Offices: Ward/Nursing, Treating Doctor, Billing, Insurance Desk (hospital), TPA, Insurer, Pharmacy.

Seeded scenarios:

| # | Scenario | Expected outcome |
| --- | --- | --- |
| H1 | Billing needs insurer final approval; insurer needs final bill + discharge summary | Cycle → alternative: provisional (interim) bill accepted by TPA → route confirmed |
| H2 | Ward withholds discharge summary until billing clearance; billing needs summary | Cycle → staff review → unresolved or approved joint processing |
| H3 | TPA asks for "investigation report", hospital calls it "lab summary" | Terminology mismatch → equivalence confirmed by authority → no conflict |
| H4 | Room-rent cap from old policy version vs current terms | Version mismatch → applicable version resolved by date |
| H5 | Pre-authorization expired due to extended stay | Expired approval → route stale → re-authorization step |
| H6 | Reply from a nurse approving a bill exception | Rejected as non-authoritative |

### 2.2 Corporate onboarding/offboarding (second)

Offices: HR, IT, Finance, Admin/Facilities, Manager.

| # | Scenario | Expected outcome |
| --- | --- | --- |
| C1 | IT needs HR exit record before revoking access; HR needs IT asset clearance before exit record | Cycle → alternative: provisional exit ticket |
| C2 | Finance full-and-final needs "no-dues"; Admin calls it "clearance form" | Terminology mismatch |
| C3 | Onboarding: laptop issue needs employee ID, ID needs signed NDA, NDA portal needs laptop login | 3-node cycle → paper NDA alternative |
| C4 | Genuinely unresolved | Unresolved report with decision request |

## 3. Case types the engine must handle

| Case type | Behavior |
| --- | --- |
| Circular prerequisites | Detect SCC; search alternatives / joint processing |
| Valid alternative (`any_of`) | Show route, no deadlock |
| Already-held document | Seed reachable set |
| Missing information | Clarification question tied to the unknown fact |
| Terminology mismatch | Request authority-confirmed equivalence |
| Version mismatch | Select rule version by effective dates; flag stale instruction |
| Incompatible conditions | Flag with sources after scope check |
| Expired approval | Mark route stale; recompute |
| Unauthorized reply | Do not record as decision |
| Case-scoped approval | Never generalized to other cases |
| Mid-call correction | Reconfirm, version, recompute, mark dependents stale |
| Genuinely stuck | Unresolved report + single decision request |

## 4. Architecture

```text
React (Vite, Tailwind, React Flow, LiveKit components)  — Cloudflare Pages
        │  REST + WebSocket                │ WebRTC
        ▼                                  ▼
FastAPI backend  ◄──── tool calls ────  LiveKit Agent worker (Python)
  │  auth (JWT roles)                    STT: Groq Whisper
  │  cases / evidence / reviews          LLM: Groq gpt-oss → OpenAI fallback
  │  rule engine (deterministic)         TTS: Deepgram Aura / Cartesia
  ├── Neon Postgres (metadata, versions, decisions, audit)
  └── Cloudflare R2 (evidence files, consented recordings, report PDFs)
```

### Pipeline

```text
Voice/Text → STT → LLM extraction (propose_requirement)
  → Readback & confirm (names, dates, negations, either/both)
  → Requirement store (unverified → verified)
  → Rule engine: reachability fixpoint over AND/OR graph
       ├ goal reachable      → candidate route
       ├ cycle / unreachable → blocking group (SCC) + missing facts
       └ unknown facts       → clarification generator
  → Staff review (authenticated, case-scoped decision)
  → Recompute → Route state: suggested → confirmed → completed | unresolved
```

Invariant: **the LLM proposes; the deterministic engine and authenticated staff decide.**

### Cloudflare R2 usage

| Prefix | Contents |
| --- | --- |
| `evidence/{case_id}/` | Uploaded discharge summaries, pre-auth letters, TPA queries, bills, photos of written instructions |
| `recordings/{case_id}/` | Consented session audio |
| `reports/{case_id}/` | Generated route summaries / unresolved-case PDFs |

Uploads use presigned PUT URLs; downloads use short-lived presigned GET URLs. Postgres stores key, SHA-256, size, MIME type, and verification status only.

## 5. Tech stack

| Layer | Choice |
| --- | --- |
| Frontend | React + Vite + TypeScript, Tailwind CSS, React Flow, `@livekit/components-react` |
| Backend | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2 + Alembic, WebSockets |
| Rule engine | Pure Python + networkx |
| Voice | LiveKit Cloud (free) + `livekit-agents` with Groq, Deepgram, Cartesia, OpenAI plugins |
| DB | Neon Postgres (free); SQLite allowed for local tests |
| Storage | Cloudflare R2 via `boto3` |
| Reports | WeasyPrint or ReportLab |
| Auth | JWT; roles `applicant`, `desk_staff`, `approver` with office-scoped authority |
| CI/Deploy | Docker, GitHub Actions (pytest + golden-case evals), Render/Fly free tier |

## 6. Data model

`Case`, `Requirement` (versioned, append-only), `Evidence`, `Authority`, `Decision`, `Route`, `Clarification`, `AuditEvent` — as described in details.md §10. Uncertainty kept as three separate fields: `transcription`, `interpretation`, `authority_verification`.

## 7. Agent tools

`get_case_context`, `lookup_approved_rules`, `propose_requirement`, `confirm_requirement`, `analyze_routes`, `prepare_clarification`, `request_staff_review` (idempotency key), `build_route_summary`.

## 8. Repository layout

```text
RuleCollision/
├─ backend/        FastAPI app, rule engine, storage, DB models, tests
├─ agent/          LiveKit voice agent worker
├─ frontend/       React app
├─ rulepacks/      hospital_discharge.yaml, corporate_lifecycle.yaml
├─ okf/            OKF v0.2 project knowledge bundle (start at okf/index.md)
├─ scripts/        check_okf.py knowledge-bundle validator
├─ AGENTS.md       Agent operating protocol
├─ docker-compose.yml
└─ .env.example
```

## 9. One-week sprint

| Day | Deliverable | Exit check |
| --- | --- | --- |
| 1 | Rule-pack schema, engine (reachability, SCC, alternatives, versions), golden cases | All H1–H6, C1–C4 tests pass |
| 2 | DB models, case/evidence APIs, R2 presigned uploads | Upload + metadata round-trip works |
| 3 | Text chat intake: extraction, readback, confirmation | Requirements confirmed only after readback |
| 4 | Staff review UI, role-scoped approvals, route states | Unauthorized approval rejected in tests |
| 5 | LiveKit voice agent, interruption + correction handling | Correction mid-call recomputes route |
| 6 | Graph view, PDF reports to R2, corporate rule pack polish | Both packs demoable |
| 7 | 3-case demo, deploy, README, video | Public demo URL |

Fallback if behind schedule: voice moves to days 6–7; text chat remains primary.

## 10. Demo script

1. **Resolved deadlock (H1):** voice intake → cycle shown in graph → clarification → approver confirms provisional bill → TPA acceptance → route confirmed.
2. **False conflict (H3):** terminology clarified → no deadlock.
3. **Unresolved (C4):** engine produces an unresolved report with a single decision request.
