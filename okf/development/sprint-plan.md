---
type: Development Plan
title: Build phases
description: Phase-by-phase deliverables and progress; replaces the one-week sprint plan.
tags: [plan, phases]
status: stable
generated: { by: claude-code/claude, at: "2026-11-10T11:25:00+00:00" }
sources:
  - id: plan
    resource: ../../PLAN.md
    title: Build plan v2
---

Plan source: [PLAN.md](../../PLAN.md) §4.[^plan] The one-week sprint was replaced by phases on 2026-11-10 ([0006](/decisions/0006-configurable-platform.md)).

| # | Deliverable | Progress |
| --- | --- | --- |
| 0 | Plan v2 and decision records 0006–0015 | **Done** |
| 1 | Backend core, demo data | **Done** (API tests passing). Engine fixes §5, §1, §6 moved to later |
| 2 | Agent settings, tool gateway, web tools, MCP registry, knowledge search, AI rule drafts | **Done** (drafting tested with a stand-in model) |
| 3 | Generic LiveKit agent | **Written**, not run live |
| 4 | Web app and QR codes | **Done** (checked in a browser locally) |
| 5 | Phone line | **Written** (phone sessions, 3-minute cap, keypad); needs a LiveKit number |
| 6 | Deployment, PDF reports, engine fixes, automated browser tests | Deploy workflow and CI written, not yet run; the rest not started |

[^plan]: Build plan v2
