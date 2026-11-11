---
type: Decision Record
title: "0019: Seed adds missing demo data on every start"
description: The demo seed runs at every backend start and adds only what is missing, so new demo data reaches an already seeded database without overwriting anything.
tags: [decision, data, operations]
status: stable
decision_status: accepted
decided_on: 2026-11-11
generated: { by: claude-code/claude, at: "2026-11-11T14:00:00+00:00" }
---

# Context

The deployed database was seeded once; the old `seed_if_empty` did nothing after that, so richer demo data would never reach it. There are no migrations yet ([0014](0014-modal-hosting-and-simple-stack.md)).

# Decision

- `seed_demo` in `backend/app/seed/demo.py` runs at every start when `SEED_DEMO=1`.
- It matches organisations by slug, staff by email, people by identifier, locations by label and knowledge documents by file name, and adds only the missing ones.
- A person's case history (cases, decisions, notes, reported rules, conversations) is written only when that person is new.
- A rule-pack version and agent profile are created only for a new organisation.
- Seeded cases get fixed case codes (`SGH…`, `NW…`) when the code is free, so "Check your case" can be demonstrated.
- All demo sign-ins use `DEMO_PASSWORD`.

# Consequences

- Staff changes in the live app are never overwritten; deleted demo people come back on the next start.
- Each start runs a few lookups; new knowledge documents are embedded once.
- Two containers starting at the same moment could both insert the same new row (see [known issues](../development/known-issues.md)).
