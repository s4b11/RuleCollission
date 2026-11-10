---
type: Decision Record
title: "0013: AI drafts rules; staff approve them"
description: The language model drafts rule-pack entries from an uploaded document or a chat with staff; nothing changes until an administrator approves, which creates a new rule-pack version.
tags: [decision, rules, llm, approval]
status: stable
decision_status: accepted
decided_on: 2026-11-10
generated: { by: claude-code/claude, at: "2026-11-10T10:50:00+00:00" }
---

# Decision

- "Draft rules from this" (Knowledge page) and the rule chat (Rules page) ask the model for a JSON proposal of offices, documents, requirements and alternatives, stored as a pending `RuleDraft`.
- The draft is checked against the active pack with the engine's loader, and problems are shown.
- An administrator can edit, approve or reject. Approval merges the draft into the active pack, validates it and saves a new `RulePackVersion`.
- The model used is Groq, then OpenAI, through `backend/app/services/llm.py`.

# Consequences

- Consistent with [0001](0001-llm-proposes-engine-decides.md): the model proposes, staff decide.
- An invalid draft cannot be approved.
