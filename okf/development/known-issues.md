---
type: Known Issues
title: Known issues and technical debt
description: Current limitations, unverified areas, technical debt and open questions.
tags: [issues, debt]
status: stable
generated: { by: claude-code/claude, at: "2026-11-10T10:52:00+00:00" }
---

# Not yet verified against live services

The agent, Modal deployment, R2 storage, Postgres, real-model rule drafting and fastembed have not run in a live environment. See [current state](/current-state.md).

# Engine limitations

Proposed resolutions: [engine limitation resolutions](engine-limitations.md). None are implemented.

- **Single producer per document after overrides.** → [§1](engine-limitations.md#1-targeted-requirement-overrides)
- **Conditions are only compared, not satisfied.** → [§2](engine-limitations.md#2-conditions-are-satisfied-not-only-compared)
- **Blocking groups are SCCs, not minimal sets.** → [§3](engine-limitations.md#3-verified-minimal-explanations-alongside-sccs)
- **Candidate search is all-or-nothing.** → [§4](engine-limitations.md#4-ranked-minimal-candidate-alternative-sets)
- **Rejected equivalences** produce no dedicated clarification, and **equivalences are not office-scoped.** → [§5](engine-limitations.md#5-clarifications-for-rejected-equivalences-scoped-per-office)
- **No engine `completed` state.** The backend marks a case `completed` when the goal document is on file, without checking who issued it. → [§6](engine-limitations.md#6-completed-route-state-and-staleness)

# Platform limitations

- **Declining an alternative's acceptance** is stored on the review request only; the engine has no such decision, so the case stays at "needs a decision".
- **Any staff member can issue or remove any document** on the dashboard; issuing is not limited to the issuing office.
- **Tool and MCP headers are stored in plain text.** They can hold credentials and should be encrypted.
- **Identification attempts are limited per session**, not per person or caller.
- **Knowledge search reads every passage** of the organisation on each query ([0009](/decisions/0009-rag-explains-engine-decides.md)).
- **Engine question wording uses internal ids** in places (for example `'interim_bill'`).
- **One agent profile per organisation** is assumed by the Studio pages.
- **Staff token is kept in browser local storage.**

# Technical debt

- No database migrations ([0014](/decisions/0014-modal-hosting-and-simple-stack.md)).
- No automated browser tests; no linter in CI.
- Unused Vite template files remain locally and are not committed: `frontend/src/App.css`, `frontend/src/assets/`, `frontend/public/icons.svg`. Safe to delete.
- The web app ships as one large script (about 900 kB).
- `AGENTS.md` §8 still says the folder is not a Git repository, and its build commands are PowerShell-only.

# Open questions

- Which LiveKit phone number, and whether a local (non-US) number is needed.
- Whether to keep one warm Modal container (uses credits) or accept cold starts.
