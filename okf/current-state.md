---
type: Status Report
title: Current state
description: Verified handover snapshot of what is implemented, unverified, blocked and next.
tags: [status, handover]
status: stable
generated: { by: claude-code/claude, at: "2026-11-10T11:25:00+00:00" }
verified:
  - { by: "process:pytest", at: "2026-11-10T10:52:00+00:00" }
---

# Snapshot (2026-11-10)

The project is now a configurable multi-organisation platform ([0006](/decisions/0006-configurable-platform.md)). Backend, web app and agent code exist. The backend and web app are tested locally; nothing has been deployed or run against live providers.

# Implemented and verified

- **Rule engine** and two rule packs: 30 golden tests ([design](/architecture/rule-engine.md)).
- **Backend API**: organisations, staff sign-in, cases, staff decisions, review inbox, agent session config, tool gateway, knowledge search, AI rule drafts, QR codes. 15 API tests ([features](/features/platform.md), [architecture](/architecture/system.md)).
- **Web app**: builds with type-checking; pages and the approve/accept flow checked in a browser locally.
- **Checks run 2026-11-10:** `pytest -q` 45 passed; `scripts/check_okf.py` passed; `npm run build` passed.

# Written but not verified

- **LiveKit agent** (`agent/`): loads against livekit-agents 1.8; config fetch and a tool call tested against a local backend. Not run in a live room: speech, model, transcript events, MCP attachment, phone dispatch, keypad input and the 3-minute cut-off are untested.
- **Deployment**: `backend/modal_app.py` loads with the Modal SDK and the [deploy workflow](/decisions/0016-deploy-with-github-actions.md) parses as valid YAML; neither has run. The workflow needs the repository secrets and must be on the default branch.
- **AI rule drafting**: tested with a stand-in model reply; not with a real model.
- **Cloudflare R2 storage path** and **Postgres**: only local disk and SQLite have run.
- **fastembed embeddings**: tests use the hashed fallback.

# Not started

PDF reports, the engine improvements in [engine limitation resolutions](/development/engine-limitations.md), database migrations, automated browser tests.

# Blockers and risks

- No provider accounts or keys are configured (LiveKit, Deepgram, Cartesia, Groq, OpenAI, Neon, R2, Modal).
- LiveKit free plan: 1,000 agent minutes and 50 inbound phone minutes a month.
- See [known issues](/development/known-issues.md).

# Next actions

1. Create provider accounts, fill `.env`, run the agent locally (`python agent.py dev`) and fix whatever the first live session shows.
2. Add the GitHub secrets, merge to the default branch, run the Deploy workflow and fix what the first run shows; then point a LiveKit number at the agent.
3. Engine fixes §5, §1 and §6 from [engine limitation resolutions](/development/engine-limitations.md).
4. Remove the unused Vite template files listed in known issues.
