---
type: Known Issues
title: Known issues and technical debt
description: Current rule-engine limitations, technical debt and open questions.
tags: [issues, debt, engine]
status: stable
generated: { by: claude-code/claude, at: "2026-11-09T03:30:00+00:00" }
---

# Engine limitations

Proposed resolutions for each item: [engine limitation resolutions](engine-limitations.md).

- **Single producer per document after overrides.** A case-reported requirement replaces every pack rule for the same `(office, produces)`; partial overrides aren't supported. → [§1](engine-limitations.md#1-targeted-requirement-overrides)
- **Conditions are only compared, not satisfied.** `conditions` are checked for conflicting values on the same document attribute, but held-document `attributes` aren't yet matched against them. → [§2](engine-limitations.md#2-conditions-are-satisfied-not-only-compared)
- **Blocking groups are SCCs, not minimal sets.** The engine doesn't compute a "smallest conflicting set" and must not claim to ([details.md](../../details.md) §6). → [§3](engine-limitations.md#3-verified-minimal-explanations-alongside-sccs)
- **Candidate search is all-or-nothing.** Candidate alternatives come from one hypothetical run with every non-refused alternative active, so it doesn't rank or minimise combinations. → [§4](engine-limitations.md#4-ranked-minimal-candidate-alternative-sets)
- **Rejected equivalences** suppress resolution but don't yet produce their own clarification. → [§5](engine-limitations.md#5-clarifications-for-rejected-equivalences-scoped-per-office)
- **Equivalences are not office-scoped** (found 2026-11-09). A confirmed `term=document` equivalence is stored by term only, so an approver from one office using the term makes it resolve for every office using that term (`resolve` in `analyzer.py`). → [§5](engine-limitations.md#5-clarifications-for-rejected-equivalences-scoped-per-office)
- **No route `completed` state.** Completion evidence will need the planned database layer. → [§6](engine-limitations.md#6-completed-route-state-and-staleness)

# Technical debt

- `backend/app/api/`, `backend/app/storage/`, `agent/` and `frontend/` don't exist yet (planned in [PLAN.md](../../PLAN.md) §8).
- No linter or CI is configured yet.

# Open questions

- Deployment target for the backend (Render vs Fly) is undecided.
