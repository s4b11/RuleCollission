---
type: Feature
title: Rule packs
description: YAML format for domain rule packs and the two fictional packs shipped with the project.
tags: [rulepacks, domains, hospital, corporate, implemented]
status: stable
generated: { by: copilot-sdk-agent/claude, at: "2026-11-08T17:39:00+05:30" }
verified:
  - { by: "process:pytest", at: "2026-11-08T17:38:00+05:30" }
sources:
  - id: hospital
    resource: ../../rulepacks/hospital_discharge.yaml
    title: Hospital discharge rule pack
  - id: corporate
    resource: ../../rulepacks/corporate_lifecycle.yaml
    title: Corporate lifecycle rule pack
---

# Format

A rule pack is one YAML file in `rulepacks/`, loaded and validated by `backend/app/engine/loader.py` ([decision 0002](/decisions/0002-domain-agnostic-rule-packs.md)).

| Key | Contents |
| --- | --- |
| `offices` | `id`, `name` |
| `documents` | `id`, `name`, optional `aliases` |
| `requirements` | `id`, `office`, `produces`, `prerequisites` (id, `all_of`, `any_of`, nested), optional `conditions`, `applies_to`, `effective_from`, `effective_until` |
| `alternatives` | `id`, `office`, `produces`, `prerequisites`, `substitutes`, `in_offices`, `approval_by`, `description` |

Pack requirements are treated as approved rules (verified). Case-reported requirements are unverified until the issuing office verifies them.

# Hospital discharge (`hospital_discharge`)

All entities are fictional.[^hospital] Seeded scenarios:

| # | Scenario | Expected outcome |
| --- | --- | --- |
| H1 | Billing needs final insurer approval; TPA needs the final bill | Cycle → `alt_interim_bill` after Billing approval and TPA acceptance |
| H2 | Doctor reportedly withholds the summary until billing clearance | Four-document cycle; unresolved once verified |
| H3 | TPA asks for an "investigation report" | Equivalence to `lab_summary` must be confirmed by the TPA |
| H4 | Old pre-authorisation rule needed a room-rent declaration | `hd_preauth_v1` before 2026-04-01, `hd_preauth_v2` after |
| H5 | Pre-authorisation expired | Must be obtained again |
| H6 | A nurse approves an exception | Rejected as unauthorised |

# Corporate lifecycle (`corporate_lifecycle`)

All entities are fictional.[^corporate]

| # | Scenario | Expected outcome |
| --- | --- | --- |
| C1 | IT needs the HR exit record; HR needs IT asset clearance | Cycle → `alt_provisional_exit` |
| C2 | Finance asks for a "clearance form" | Approved alias of `no_dues_certificate` |
| C3 | Employee ID ↔ e-signed NDA ↔ laptop | Three-node cycle → `alt_paper_nda` |
| C4 | Security reportedly verifies only after the joining letter | Unresolved once verified |

[^hospital]: Hospital discharge rule pack
[^corporate]: Corporate lifecycle rule pack
