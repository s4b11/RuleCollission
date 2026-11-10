---
type: Decision Record
title: "0006: Configurable platform with a hospital showcase"
description: RuleCollision is a multi-organisation platform any domain can configure; the fictional hospital is the showcase and phases replace the one-week sprint.
tags: [decision, scope, tenancy]
status: stable
decision_status: accepted
decided_on: 2026-11-10
generated: { by: claude-code/claude, at: "2026-11-10T10:50:00+00:00" }
---

# Context

The user asked for an abstract product usable in any domain, owned and configured by the organisation, with the hospital as the demonstration.

# Decision

- Every record belongs to an `Organization`. An organisation owns its rule packs, agent profile, tools, MCP servers, knowledge documents, staff and subjects.
- People the agent serves are generic `Subject` rows (identifier, optional second factor, free-form `details`). Hospital fields such as ward and bed live in `details`, so the core has no hospital code ([0002](0002-domain-agnostic-rule-packs.md)).
- The seeded fictional hospital is the showcase. The fictional company stays as a second organisation to prove the platform is generic.
- The build is phased instead of a one-week sprint. This replaces the goal and timeline rows of [0005](0005-deepgram-cartesia-speech.md); its provider choices stand.

# Consequences

- Every API query filters by the signed-in user's organisation; a test covers cross-organisation access.
- The "mock hospital system" is the seeded `Subject` and `SubjectDocument` data, edited from the staff dashboard.
