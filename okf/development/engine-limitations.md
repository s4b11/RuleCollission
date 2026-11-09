---
type: Development Plan
title: Engine limitation resolutions (proposed)
description: Proposed designs, golden tests and sequencing for resolving each known rule-engine limitation. Nothing here is implemented.
tags: [engine, plan, proposed, debt]
status: draft
generated: { by: claude-code/claude, at: "2026-11-09T03:30:00+00:00" }
sources:
  - id: analyzer
    resource: ../../backend/app/engine/analyzer.py
    title: Analyzer source
  - id: models
    resource: ../../backend/app/engine/models.py
    title: Engine models
  - id: concept
    resource: ../../details.md
    title: Project concept, section 6
---

> **Status: proposed.** Each item resolves one entry in [known issues](known-issues.md). All of it must stay deterministic, domain-agnostic ([0002](/decisions/0002-domain-agnostic-rule-packs.md)) and must never let unverified input confirm a route ([0001](/decisions/0001-llm-proposes-engine-decides.md)). Every item ships with golden tests in `backend/tests/` for both packs where applicable.[^analyzer]

# 1. Targeted requirement overrides

**Today:** a case-reported requirement removes *every* pack rule with the same `(office, produces)` (`overridden` set in `analyze`).

**Proposal:**
- Add to `Requirement`: `mode: replace | add_prerequisites` (default `replace`) and `overrides: list[str]` (pack rule ids).
- `replace` removes only the rules listed in `overrides`; `add_prerequisites` keeps the pack rule and ANDs the reported prerequisites onto it (`{all_of: [pack_expr, reported_expr]}`), producing one merged producer that keeps both requirement ids for evidence.
- If `overrides` is empty and more than one pack rule produces the same document for that office, do not guess: keep all pack rules, treat the reported rule as unscoped, and raise a new `override_scope` clarification ("Which of these procedures does this instruction replace?") to the issuing office. With exactly one candidate rule, target it implicitly (current behaviour, now explicit).
- `cites_rule` stays for version checks; when set it also implies `overrides: [cites_rule]`.

**Tests:** a pack with two producers for one document where a report overrides only one (route via the other survives); `add_prerequisites` turning H2 into a merged requirement whose blocking group lists both ids; an ambiguous override producing `override_scope`.

# 2. Conditions are satisfied, not only compared

**Today:** `conditions` are grouped per `(document, attribute)` across all relevant requirements and flagged when values differ; `HeldDocument.attributes` are never read.

**Proposal:**
- Extend `Condition` with an operator: `equals` (existing) or `in: [..]`.
- Let rule-pack producers declare what they issue: `issues_with: {attribute: value}` on requirements and alternatives (e.g. `alt_interim_bill` issues `status: provisional`).
- Track attributes in reachability: `reach` stores, per document, the attribute set from the held document or from its chosen producer. In `_evaluate`, an atom is usable for a requirement only if its attributes satisfy that requirement's conditions on that document. An unknown attribute (held document without it, producer not declaring it) makes the atom *conditionally* usable and raises a `missing_attribute` clarification ("Is the held lab summary signed by a pathologist?"); a route that relies on it stays `suggested`.
- Report `condition_conflict` only when two requirements **on the chosen route** need different values for the **same document instance** and no producer can issue a copy for each. Conflicts among relevant-but-unused requirements become informational notes, not a `needs_decision` outcome.

**Tests:** held document with matching / mismatching / missing attribute; an alternative whose `issues_with` violates a downstream condition (route blocked, not confirmed); the existing `test_incompatible_conditions_are_flagged` stays green; a conflict off the chosen route no longer downgrades the outcome.

# 3. Verified minimal explanations alongside SCCs

**Today:** blocking groups are strongly connected components of the unreachable dependency graph. That is correct but can be large, and `details.md` §6 forbids calling it a "smallest conflicting set" unless computed and verified.[^concept]

**Proposal:** keep SCCs as `blocking_groups` and add two optional, *verified* explanations per group:
- **`shortest_cycle`**: the shortest directed cycle inside the SCC (BFS from each node, or `nx.simple_cycles(sub, length_bound=k)` with increasing `k`). This is easy to explain ("A needs B, B needs A") and its minimality is by construction.
- **`irreducible_unblocking_set`**: a set-minimal set of requirement ids whose prerequisites, if waived, make the goal reachable. Compute it by deletion filtering: start with every requirement in the SCC waived (goal reachable), then try un-waiving each in deterministic id order and keep it un-waived if the goal stays reachable. Then *verify* by rechecking that removing any single member breaks reachability, and set `verified: true` only if that check passes.
- Wording: "irreducible" (set-minimal), never "smallest" (cardinality-minimal is NP-hard in general and not computed). The set tells staff exactly which rules a decision must touch, which sharpens the single `decision_request`.

**Tests:** H1 shortest cycle is the two-node billing/TPA cycle; C3 returns the three-node cycle; a constructed SCC with a nested two-cycle reports the two-cycle as shortest; the unblocking set is verified and each member is necessary.

# 4. Ranked, minimal candidate alternative sets

**Today:** one hypothetical run with every non-refused alternative active; candidates are whatever that run used. No ranking, and unnecessary alternatives can appear.

**Proposal:**
- Prune to relevant alternatives: those whose `substitutes` (or `produces`) lies in the goal's ancestor set and is currently unreachable.
- Enumerate subsets by increasing size, cap at `MAX_ALTERNATIVES` (e.g. 8 relevant alternatives, 256 runs, each a cheap fixpoint). Keep only **minimal sufficient sets** (goal reachable, no proper subset sufficient). Above the cap, fall back to the deletion filter from §3 to return one set-minimal set.
- Rank deterministically by: number of alternatives → outstanding decisions (approvals + acceptances not yet recorded) → number of distinct offices involved → route length → ids.
- Output `candidate_sets: list[CandidateSet]` (alternatives, pending approvals/acceptances, rank). Keep `candidate_alternatives` as the top set for backward compatibility. Raise approval/acceptance clarifications **only for the top-ranked set**, so staff aren't asked about every option at once.

**Tests:** a pack with two independent alternatives that each unlock the goal (two singleton sets, ranked by pending decisions); a pack where the all-on run used a redundant alternative (it no longer appears); a refused alternative never appears in any set; H1 and C3 results unchanged.

# 5. Clarifications for rejected equivalences, scoped per office

**Today:** a `reject_equivalence` just stops resolution, and the term falls through to a generic `missing_document` question. Also, a confirmed equivalence is stored by term only, so one office's confirmation is applied to every office that uses the same term (newly found; see [known issues](known-issues.md)).

**Proposal:**
- Key equivalences by `(term, office)`: decision target becomes `term=document@office`, with the current `term=document` form accepted as shorthand for the deciding approver's office. `resolve` takes the requiring office as a parameter.
- On rejection, add a `rejected_equivalence` note and a dedicated clarification to that office: "{office} does not accept '{document}' as '{term}'. Which document does it require, and which office issues it?" Do not also emit the generic `missing_document` question for that term.
- A later `confirm_equivalence` by an authorised approver supersedes an earlier rejection only if it is newer. This needs a decision timestamp (`decided_at`) on `Decision`.

**Tests:** H3 rejected by the TPA yields the dedicated clarification; TPA's confirmation does not resolve the same term used by Billing; confirm-after-reject resolves the term.

# 6. `completed` route state and staleness

**Today:** `RouteStatus` is `suggested | confirmed`; a held goal returns an empty `confirmed` route.

**Proposal (engine part, independent of the database):**
- Add `HeldDocument.verified_by: StaffIdentity | None` and `evidence_id`. Add `RouteStatus.completed`, returned when the goal is held *and* that holding is verified by staff of the issuing office or by a verified evidence record. An unverified held goal is reported as `confirmed` with a `verify_holding` clarification.
- Make each `Analysis` include an `inputs_fingerprint`: a hash of the effective rule ids and versions, valid decision ids with `valid_until`, held documents, and the pack version. A stored route whose fingerprint differs from a recomputation is **stale**. This implements PLAN.md's "expired approval → route stale" and "mid-call correction → mark dependents stale".

**Database part (sprint days 2 and 4):** persist `Route` rows with the fingerprint and status history (`suggested → confirmed → completed`, or `unresolved`), and recompute on every change to requirements, decisions or evidence.

**Tests:** held goal with and without verification; fingerprint changes when a decision expires (H5) and when a requirement is corrected (`both` → `either`).

# Sequencing

| Order | Item | Why this order | Fits sprint |
| --- | --- | --- | --- |
| 1 | §5 Equivalence scoping and rejection clarification | Small and fixes a real correctness gap (one office's confirmation applied to others) | Day 2, before staff decisions are persisted |
| 2 | §1 Targeted overrides | Needed before text intake (day 3) starts storing reported requirements | Day 2–3 |
| 3 | §6 `completed` + fingerprint | Defines the route record the database stores | Day 2 (models), day 4 (review UI) |
| 4 | §4 Candidate sets | Improves the H1/C1/C3 demo and staff review | Day 4 |
| 5 | §3 Verified minimal explanations | Improves the graph view and the unresolved report | Day 6 |
| 6 | §2 Condition satisfaction | Largest change to `_evaluate`/`_reach`; only needed once evidence attributes are captured | After day 6, or day 6 if time allows |

[^analyzer]: Analyzer source
[^concept]: Project concept, section 6
