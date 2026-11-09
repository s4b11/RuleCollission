---
type: Architecture
title: Rule engine
description: Deterministic AND/OR prerequisite reachability, blocking-group detection and authority validation in backend/app/engine.
resource: ../../backend/app/engine/analyzer.py
tags: [engine, deterministic, implemented]
status: stable
generated: { by: copilot-sdk-agent/claude, at: "2026-11-08T17:39:00+05:30" }
verified:
  - { by: "process:pytest", at: "2026-11-08T17:38:00+05:30" }
sources:
  - id: analyzer
    resource: ../../backend/app/engine/analyzer.py
    title: Analyzer source
  - id: models
    resource: ../../backend/app/engine/models.py
    title: Engine models
  - id: loader
    resource: ../../backend/app/engine/loader.py
    title: Rule-pack loader and validator
---

# Modules

| File | Responsibility |
| --- | --- |
| `backend/app/engine/models.py` | Pydantic models: rule pack, requirement, alternative, case, decision, analysis output |
| `backend/app/engine/loader.py` | Loads `rulepacks/*.yaml`; validates offices, documents, aliases, prerequisites and duplicate ids |
| `backend/app/engine/analyzer.py` | `analyze(pack, case) -> Analysis` |

Dependencies: `pydantic`, `networkx`, `pyyaml` (see `backend/pyproject.toml`). No network calls, no LLM.

# Algorithm

1. **Effective rules.** Use pack requirements in force on `case.as_of` that apply to the applicant category. A case-reported requirement replaces the pack rule for the same `(office, produces)`. A reported instruction citing a rule not in force on that date is dropped with a `version_mismatch` note.[^analyzer]
2. **Decisions.** Each decision is checked for case scope, expiry and authority (see the table below); invalid ones are ignored and reported as notes.
3. **Term resolution.** A term resolves to a document id, then a pack alias, then a case-confirmed equivalence.
4. **Held documents.** Expired holdings are excluded and noted.
5. **Reachability.** A fixed-point loop over AND/OR expressions; each round adds every newly producible document. Active alternatives add their document and act as substitutes only in their accepting offices.
6. **Route.** Walk back from the goal through the chosen producers. The route is `confirmed` only if every requirement used is verified and there are no condition conflicts; otherwise it is `suggested`.
7. **Blockage.** If the goal is unreachable, build the graph of unreachable, relevant dependencies and report strongly connected components as blocking groups, with their requirement sources.
8. **Candidates.** Rerun reachability as if every non-refused alternative were active; report alternatives on that hypothetical route with approval and acceptance still pending.
9. **Outcome.** `needs_decision` if a candidate exists; otherwise `needs_information` for missing documents, unconfirmed equivalences or unverified blocking requirements; otherwise `unresolved` with a single decision request.

# Authority rules

| Decision | Valid only when made by |
| --- | --- |
| `verify_requirement` | Desk staff or approver of the requirement's issuing office |
| `approve_alternative` / `refuse_alternative` | Approver of the alternative's `approval_by` office |
| `accept_alternative` | Approver of an office in `in_offices` |
| `confirm_equivalence` / `reject_equivalence` | Approver of an office that uses the term |

All decisions must belong to the same case and must not have expired. Applicants can never record decisions.[^analyzer]

# Limitations

See [known issues](/development/known-issues.md).

Related: [route analysis behavior](/features/route-analysis.md), [decision 0001](/decisions/0001-llm-proposes-engine-decides.md).

[^analyzer]: Analyzer source
