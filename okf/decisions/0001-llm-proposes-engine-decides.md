---
type: Decision Record
title: "0001: LLM proposes, engine and staff decide"
description: Language-model output can only propose requirements; deterministic code and authorised staff decide outcomes.
tags: [decision, safety, engine]
status: stable
decision_status: accepted
decided_on: 2026-11-08
generated: { by: copilot-sdk-agent/claude, at: "2026-11-08T17:39:00+05:30" }
sources:
  - id: concept
    resource: ../../details.md
    title: Project concept, sections 6, 11 and 13
---

# Context

The product's value depends on never presenting an unsupported route as confirmed. Language models can misread "either" as "both", invent equivalences or sound confident about authority they do not have.[^concept]

# Decision

- The LLM may only propose candidate requirements linked to evidence, and draft clarification wording.
- Reachability, blockage and route status are computed by deterministic code in `backend/app/engine/`.
- Verifications, approvals, acceptances and equivalences count only when recorded by an authenticated staff member with the required office and role.

# Consequences

- Route analysis is reproducible and testable without any provider.
- Requirements reported by the applicant stay unverified, and routes using them stay `suggested`.
- The voice agent needs readback and confirmation steps before saving requirements.

Implemented in the [rule engine](/architecture/rule-engine.md).

[^concept]: Project concept, sections 6, 11 and 13
