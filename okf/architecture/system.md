---
type: Architecture
title: System architecture
description: Components, request flows, data model and security boundaries of the platform as implemented.
tags: [architecture, backend, agent, frontend]
status: stable
generated: { by: claude-code/claude, at: "2026-11-10T10:52:00+00:00" }
verified:
  - { by: "process:pytest", at: "2026-11-10T10:52:00+00:00" }
sources:
  - id: plan
    resource: ../../PLAN.md
    title: Build plan v2
  - id: main
    resource: ../../backend/app/main.py
    title: Backend entry point
  - id: agent
    resource: ../../agent/agent.py
    title: LiveKit agent
---

> Backend and web app are implemented and tested. The agent is written and its backend calls are tested, but it has not run against live LiveKit, speech or model services.[^plan]

# Components

| Part | Location | Role |
| --- | --- | --- |
| Backend | `backend/app/` | FastAPI app[^main] |
| Rule engine | `backend/app/engine/` | [Deterministic analysis](/architecture/rule-engine.md) |
| Agent | `agent/` | One generic LiveKit worker[^agent] ([0007](/decisions/0007-single-dynamic-agent.md)) |
| Web app | `frontend/` | Patient assistant, staff dashboard, Agent Studio |

# Backend layout

| Module | Contents |
| --- | --- |
| `models.py` | All tables |
| `api/auth.py` | Staff sign-in |
| `api/public.py` | Patient page: agent info, start session, session state, case lookup, QR image |
| `api/ops.py` | Staff dashboard: subjects, documents, cases, review inbox, transcripts |
| `api/studio.py` | Administrators: agent profile, tools, MCP, locations, knowledge, rule packs, drafts |
| `api/agent_internal.py` | Agent only: session config, phone sessions, tool calls, transcripts |
| `services/cases.py` | Builds the engine input, stores the analysis, syncs review requests, records decisions |
| `services/summary.py` | Readable case summary and dependency graph |
| `services/agent_config.py` | Session instructions and tool list |
| `services/rule_drafts.py`, `services/llm.py` | AI rule drafts |
| `rag/` | Document ingest, embedding, search |
| `tools/` | Built-in tools and the external web-tool caller |
| `seed/demo.py` | Fictional hospital and company |

# Main flows

**Conversation.** The patient page asks the backend for a session and a LiveKit token. LiveKit dispatches the agent with the session id. The agent fetches its configuration, registers tools from their schemas, and forwards every tool call to the backend. The page polls the session state to show the case.

**Case analysis.** `services/cases.analyze_case` loads the active rule pack, converts the case, the subject's documents, reported requirements and staff decisions into engine models, runs `analyze`, stores the result and creates one `ReviewRequest` per clarification.

**Staff decision.** A staff member answers a review request. The backend records a `Decision` and reruns the engine. If the engine rejects the decision for lack of authority, the decision is removed and the request returns 403.

**Rule drafting.** See [0013](/decisions/0013-ai-rule-drafts.md).

# Data model

`Organization`, `StaffUser`, `RulePackVersion`, `RuleDraft`, `AgentProfile`, `ToolDefinition`, `McpServer`, `Location`, `KnowledgeDocument`, `KnowledgeChunk`, `Subject`, `SubjectDocument`, `Case`, `Decision`, `ReviewRequest`, `CaseNote`, `AgentSession`, `TranscriptLine`, `ToolInvocation`. Reported requirements and equivalence claims are JSON on the case.

# Security boundaries

- Staff APIs need a JWT; every query filters by the staff member's organisation. Studio APIs need `is_admin`.
- Agent APIs need the shared `AGENT_API_KEY`.
- Patient session state needs the session's secret token; case lookup needs code and identifier.
- Tools cannot record decisions; external addresses must be public `https` ([0010](/decisions/0010-tools-read-propose-note.md)).

# Deployment

Backend on Modal (`backend/modal_app.py`, scales to zero, see [0018](/decisions/0018-modal-scale-to-zero.md)), agent on LiveKit Cloud (`agent/Dockerfile`), web app on a static host. Settings: `.env.example`. See [0014](/decisions/0014-modal-hosting-and-simple-stack.md).

[^plan]: Build plan v2
[^main]: Backend entry point
[^agent]: LiveKit agent
