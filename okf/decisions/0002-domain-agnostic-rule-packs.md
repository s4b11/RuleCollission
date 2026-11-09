---
type: Decision Record
title: "0002: Domain-agnostic rule packs"
description: Each domain is a YAML rule pack consumed by one generic engine, so new domains need no code changes.
tags: [decision, rulepacks, architecture]
status: stable
decision_status: accepted
decided_on: 2026-11-08
generated: { by: copilot-sdk-agent/claude, at: "2026-11-08T17:39:00+05:30" }
---

# Context

The user asked for an app that handles every kind of case, with hospital discharge as the main domain and corporate onboarding/offboarding as a second domain proving it generalises.

# Decision

Domain knowledge (offices, documents, aliases, requirements, versions, alternatives) lives in `rulepacks/*.yaml`. The engine contains no domain-specific logic. The loader validates every pack before use.

# Alternatives considered

- Hard-coded workflows per domain: rejected, because it doesn't generalise and makes the "every case" claim untestable.

# Consequences

- A domain is added by writing a YAML file and golden tests.
- Expressiveness is limited to the rule-pack schema ([known issues](/development/known-issues.md)).

See [rule packs](/features/rule-packs.md).
