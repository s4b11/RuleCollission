---
type: Feature
title: Platform features
description: What the patient assistant, staff dashboard, Agent Studio and agent tools do, and which tests cover them.
tags: [features, dashboard, studio, agent, implemented]
status: stable
generated: { by: claude-code/claude, at: "2026-11-11T14:00:00+00:00" }
verified:
  - { by: "process:pytest", at: "2026-11-11T14:00:00+00:00" }
sources:
  - id: tests
    resource: ../../backend/tests/test_api.py
    title: API tests
---

# Patient assistant (`/a/{profile}`, `/case`)

- Opened by link or QR code; the location label is passed to the agent.
- Talk or type in a LiveKit room; live transcript; the case summary and dependency graph appear once the person is identified.
- `/case` shows a case from its code and the person's identifier.

# Staff dashboard (`/ops`)

| Page | What staff can do |
| --- | --- |
| Overview | Counts, questions for their office, recent cases |
| Patients (label set per organisation) | Bed board when records have wards, full list, start a case |
| Cases, case page | Summary, dependency graph, questions, documents on file (issue or remove), reported rules, decisions, notes, transcripts |
| Review inbox | Answer questions for their office; each answer applies to one case |
| Conversations | Transcripts of web and phone sessions |

# Agent Studio (`/studio`, administrators)

| Page | Settings |
| --- | --- |
| Agent | Name, greeting, extra instructions, speech providers, voice, identifier, built-in tools, preview of what the agent receives |
| Tools and MCP | Web tools (address, method, JSON schema) and MCP servers |
| Knowledge | Upload, delete, test search, draft rules from a document |
| Rules | Approved rules, drafts to approve, rule chat, file editor, version history |
| QR codes and phone | Locations with printable QR codes, linked phone number |

# Demo data

`backend/app/seed/demo.py` (all fictional), added on every start without touching existing rows ([0019](/decisions/0019-seed-adds-missing-demo-data.md)):

| | Sunrise General Hospital | Northwind Labs |
| --- | --- | --- |
| Staff sign-ins | 12 (every office in the pack) | 8 (every office in the pack) |
| People | 26 patients | 14 employees |
| Cases | 18, fixed codes `SGH…` | 11, fixed codes `NW…` |
| Shown states | deadlock, interim bill approved and accepted, approved but not yet accepted, refused (stuck), reported rule to verify, unconfirmed name ("investigation report"), expired pre-authorisation, completed | offboarding deadlock, provisional exit approved and accepted, reported settlement rule, onboarding NDA loop, paper NDA approved and accepted, background check pending, completed |
| Extras | notes, 4 past conversations (web and phone), 6 QR locations, 2 knowledge documents | notes, 2 past conversations, 3 QR locations, 1 knowledge document |

All sign-ins use `DEMO_PASSWORD`. Only approvers can approve or accept alternatives; desk staff are refused.

# Agent tools

Listed in [decision 0010](/decisions/0010-tools-read-propose-note.md). Case tools return an error until `identify_subject` succeeds.

# Test coverage

| Behaviour | Test in `backend/tests/test_api.py`[^tests] |
| --- | --- |
| Deadlock resolved by Billing approval and TPA acceptance; nurse refused | `test_h1_deadlock_resolved_by_staff_decisions` |
| Issuing the goal document completes the case | `test_issuing_the_goal_document_completes_the_case` |
| Agent endpoints need the key | `test_agent_endpoints_need_the_agent_key` |
| Prompt and tool changes reach the next session; phone cap is 180 s | `test_session_config_is_built_from_the_database` |
| Identification with second check and attempt count | `test_agent_must_identify_before_case_tools` |
| Proposals stay unverified; no decision tool exists | `test_agent_proposals_stay_unverified_and_cannot_decide` |
| Knowledge search cites the document | `test_knowledge_search_returns_cited_passages` |
| Organisations are isolated | `test_organisations_cannot_see_each_other` |
| Studio is admin-only | `test_only_admins_open_the_studio` |
| Drafts change rules only after approval; invalid drafts refused | `test_rule_draft_needs_staff_approval`, `test_invalid_rule_draft_is_refused` |
| External tools cannot reach private addresses | `test_external_tools_cannot_reach_private_addresses` |
| Seeding twice adds nothing; an old database gains the new data; seeded cases reach their intended states; every seeded user signs in | `backend/tests/test_seed.py` |
| Case lookup and QR link | `test_public_case_lookup_needs_code_and_identifier`, `test_qr_code_points_to_the_web_app` |

The interface follows [decision 0017](/decisions/0017-polished-dashboard-design.md). Browser checks on 2026-11-10 after the redesign (Playwright, local, 1440 px and phone width): all pages render without console errors; nurse refused, Billing approves, TPA accepts, route confirmed; rule chat shows a clear message when no model key is set. On 2026-11-11 a phone-layout bug was fixed (page grids widened to fit their widest table or graph); every staff, studio and patient page was then measured at 390 px and 360 px wide and none is wider than the screen. Pages show a loading spinner until their first data arrives, and an error with "Try again" if it fails; buttons that call the backend show a spinner and are disabled while waiting (checked 2026-11-11 with every request delayed by 1.5 s). Not covered by an automated browser test in the repository.

[^tests]: API tests
