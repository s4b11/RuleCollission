# RuleCollision — Build Plan (v2)

> A voice and text assistant, configurable by any organisation, that finds requirements blocking each other across offices and ends each case with a route, a targeted question, or an evidence-backed "stuck" report.

Concept: [details.md](./details.md). Current status, decisions and known issues: [okf/](./okf/index.md). This plan replaces the one-week, single-purpose plan of 2026-11-08.

## 1. Decisions

| Topic | Decision |
| --- | --- |
| Product shape | Multi-organisation platform; each organisation owns its rule packs, agent settings, tools, documents, staff and records |
| Showcase | Fictional hospital (discharge with cashless insurance); a fictional company is the second organisation |
| Channels | Web app opened by QR code (voice and text); phone line through LiveKit telephony |
| Agent | One generic LiveKit agent; fixed safety prompt in code, everything else loaded per session |
| Tools | Built-in tools, admin-defined web tools and MCP servers, all configured in Agent Studio; none can record a decision |
| Knowledge | Uploaded documents searched for answers with citations; never used to decide a case |
| Rule authoring | AI drafts rules from documents or chat; an administrator approves |
| Speech | Deepgram (primary) and Cartesia (alternate) for both speech-to-text and text-to-speech |
| LLM | Groq `openai/gpt-oss-120b`; fallback OpenAI `gpt-5.4-mini` |
| Realtime | LiveKit (WebRTC) for conversations; dashboards poll; no application WebSockets |
| Limits | Phone calls end after 3 minutes; web sessions have no cap |
| Records | Text transcripts only; no audio recording; no SMS |
| Hosting | Backend on Modal, Neon Postgres, Cloudflare R2, static web app |
| Language and budget | English; free tiers where possible |
| Code and design | Simple code with few comments; flat neutral dashboard, no neon or gradients |

Each row has a decision record in [okf/decisions/](./okf/decisions/index.md).

## 2. Invariants

1. The AI proposes; the deterministic engine and signed-in staff decide.
2. Domain behaviour lives in rule packs, not in code.
3. All demo data is fictional. No secrets in the repository.

## 3. Architecture

```text
 QR code ─▶ Patient web app ─┐                     ┌─ Phone caller
 Staff dashboard             │ WebRTC              │ SIP
 Agent Studio                ▼                     ▼
      │ HTTPS            LiveKit Cloud ──────▶ one generic agent (agent/)
      ▼                                             │ HTTPS: config + tool calls
 FastAPI backend (backend/, hosted on Modal) ◀──────┘
  ├ rule engine  analyze(pack, case)
  ├ cases, staff decisions, review requests, transcripts
  ├ agent profiles, tool gateway, MCP registry, QR codes
  ├ knowledge search and AI rule drafts
  ├ Postgres (SQLite locally)
  └ Cloudflare R2 (local disk locally)
```

## 4. Phases

| # | Deliverable | State |
| --- | --- | --- |
| 0 | Plan and decision records | Done |
| 1 | Backend core: organisations, staff sign-in, rule-pack versions, cases on the engine, staff decisions, demo data | Done |
| 2 | Agent settings, tool gateway, web tools, MCP registry, knowledge search, AI rule drafts | Done |
| 3 | Generic LiveKit agent | Written; not yet run against live services |
| 4 | Web app: patient assistant, staff dashboard, Agent Studio, QR codes | Done |
| 5 | Phone line | Agent and backend support written; needs a LiveKit number to test |
| 6 | Deployment, PDF reports, engine improvements | Deployment files written; reports and engine improvements not started |

Detail and remaining work: [okf/development/sprint-plan.md](./okf/development/sprint-plan.md).

## 5. Demo script

1. **Resolved deadlock:** a patient asks why discharge is stuck; the graph shows Billing and the TPA waiting on each other; Billing approves an interim bill; the TPA accepts it; the route is confirmed.
2. **Authority check:** a ward nurse tries to approve the same exception and is refused.
3. **Rule authoring:** an administrator describes a rule in chat, reviews the draft and approves it as a new rule-pack version.
4. **Second organisation:** sign in to the fictional company and see only its own data.
