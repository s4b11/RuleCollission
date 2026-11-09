---
type: Feature
title: Route analysis
description: Case types handled by the rule engine and the outcome, notes and clarifications produced for each.
tags: [engine, case-types, implemented]
status: stable
generated: { by: copilot-sdk-agent/claude, at: "2026-11-08T17:39:00+05:30" }
verified:
  - { by: "process:pytest", at: "2026-11-08T17:38:00+05:30" }
sources:
  - id: tests-hospital
    resource: ../../backend/tests/test_hospital.py
    title: Hospital golden tests
  - id: tests-corporate
    resource: ../../backend/tests/test_corporate.py
    title: Corporate golden tests
---

# Outcomes

| `status` | Meaning |
| --- | --- |
| `route_available` | A route exists. `route.status` is `confirmed` when every requirement used is verified, otherwise `suggested`. |
| `needs_information` | Missing documents, unconfirmed equivalences or unverified blocking requirements |
| `needs_decision` | An alternative could unlock the goal, or conditions conflict; approval or acceptance is pending |
| `unresolved` | Verified cycle with no usable alternative; one `decision_request` clarification is produced |

# Case types and test coverage

Each row is covered by a test in `backend/tests/`.[^tests-hospital][^tests-corporate]

| Case type | Engine behavior | Test |
| --- | --- | --- |
| Circular prerequisites | Blocking group (SCC) with requirement sources | `test_h1_cycle_detected_with_candidate_alternative`, `test_c3_three_node_cycle_and_paper_nda` |
| Alternative approved and accepted | Route confirmed via alternative | `test_h1_route_confirmed_after_approval_and_acceptance` |
| Approval without acceptance | Stays `needs_decision` | `test_h1_approval_without_acceptance_is_not_enough` |
| Unverified reported cycle | `needs_information` + `verify_requirement` | `test_h2_unverified_cycle_needs_information` |
| Verified cycle, no alternative | `unresolved` + `decision_request` | `test_h2_verified_cycle_is_unresolved_with_decision_request`, `test_c4_verified_cycle_without_alternative_is_unresolved` |
| Terminology mismatch | `unconfirmed_equivalence` clarification; resolved after authorised confirmation | `test_h3_*` |
| Approved alias | Silent resolution with `equivalence_applied` note | `test_c1_route_after_provisional_exit_ticket` |
| Outdated instruction | `version_mismatch` note; current rule used | `test_h4_*` |
| Expired document / decision | Excluded with a note | `test_h5_*` |
| Unauthorised decision | Ignored with `rejected_decision` note | `test_h6_*`, `test_applicant_cannot_record_decisions`, `test_staff_from_other_office_cannot_verify` |
| Decision from another case | Ignored | `test_decision_from_another_case_is_not_reused` |
| Refused alternative | `unresolved` | `test_c3_refused_alternative_leaves_case_unresolved` |
| Already-held prerequisite or goal | Cycle broken / empty route | `test_held_prerequisite_breaks_cycle`, `test_goal_already_held`, `test_c1_already_holding_exit_record_needs_no_alternative` |
| Unknown document | `missing_document` clarification | `test_unknown_document_is_missing_information` |
| Incompatible conditions | `condition_conflict`; route only `suggested` | `test_incompatible_conditions_are_flagged` |
| Applicant category | Asks when unknown; filters when known | `test_applicability_unknown_asks_and_known_category_filters` |
| Correction "both" → "either" | Outcome recomputed from the corrected expression | `test_correction_from_both_to_either_changes_outcome` |
| Invalid rule pack | `RulePackError` | `test_invalid_rulepack_rejected` |

Not yet handled: see [known issues](/development/known-issues.md). Design: [rule engine](/architecture/rule-engine.md).

[^tests-hospital]: Hospital golden tests
[^tests-corporate]: Corporate golden tests
