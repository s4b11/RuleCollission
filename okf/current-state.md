---
type: Status Report
title: Current state
description: Verified handover snapshot of what is implemented, unverified, blocked and next.
tags: [status, handover]
status: stable
generated: { by: claude-code/claude, at: "2026-11-10T21:59:00+00:00" }
verified:
  - { by: "process:pytest", at: "2026-11-10T10:52:00+00:00" }
---

# Snapshot (2026-11-10)

The project is a configurable multi-organisation platform ([0006](/decisions/0006-configurable-platform.md)). On 2026-11-10 the first deploy succeeded: backend on Modal (health check passed in the job), agent on LiveKit Cloud (reported running), web app on Cloudflare Pages. No live conversation has been confirmed yet. The web app was then redesigned ([0017](/decisions/0017-polished-dashboard-design.md)).

# Implemented and verified

- **Rule engine** and two rule packs: 30 golden tests ([design](/architecture/rule-engine.md)).
- **Backend API**: organisations, staff sign-in, cases, staff decisions, review inbox, agent session config, tool gateway, knowledge search, AI rule drafts, QR codes. 15 API tests ([features](/features/platform.md), [architecture](/architecture/system.md)).
- **Web app**: builds with type-checking; pages and the approve/accept flow checked in a browser locally.
- **Checks run 2026-11-10:** `pytest -q` 45 passed; `scripts/check_okf.py` passed; `npm run build` passed.

# Written but not verified

- **LiveKit agent** (`agent/`): loads against livekit-agents 1.8; config fetch and a tool call tested against a local backend. Not run in a live room: speech, model, transcript events, MCP attachment, phone dispatch, keypad input and the 3-minute cut-off are untested.
- **Live use after deployment**: the [deploy workflow](/decisions/0016-deploy-with-github-actions.md) ran green once (run 42842630005), but sign-in, the staff flow and a conversation on the deployed site have not been confirmed.
- **AI rule drafting**: tested with a stand-in model reply; not with a real model.
- **Cloudflare R2 storage path** and **Postgres**: only local disk and SQLite have run.
- **fastembed embeddings**: tests use the hashed fallback.

# Not started

PDF reports, the engine improvements in [engine limitation resolutions](/development/engine-limitations.md), database migrations, automated browser tests.

# Blockers and risks

- GitHub Actions minutes for private repositories are used up on the owner's account; the repository was made public so the deploy workflow can run.
- LiveKit free plan: 1,000 agent minutes and 50 inbound phone minutes a month.
- See [known issues](/development/known-issues.md).

# Next actions

1. Confirm sign-in, the staff flow and one conversation on the deployed site; fix what the first live session shows.
2. Point a LiveKit phone number at the agent.
3. Engine fixes §5, §1 and §6 from [engine limitation resolutions](/development/engine-limitations.md).
4. Remove the unused Vite template files listed in known issues.
