---
type: Known Issues
title: Known issues and technical debt
description: Current rule-engine limitations, technical debt and open questions.
tags: [issues, debt, engine]
status: stable
generated: { by: copilot-sdk-agent/claude, at: "2026-11-08T17:39:00+05:30" }
---

# Engine limitations

- **Single producer per document after overrides.** A case-reported requirement replaces every pack rule for the same `(office, produces)`; partial overrides aren't supported.
- **Conditions are only compared, not satisfied.** `conditions` are checked for conflicting values on the same document attribute, but held-document `attributes` aren't yet matched against them.
- **Blocking groups are SCCs, not minimal sets.** The engine doesn't compute a "smallest conflicting set" and must not claim to ([details.md](../../details.md) §6).
- **Candidate search is all-or-nothing.** Candidate alternatives come from one hypothetical run with every non-refused alternative active, so it doesn't rank or minimise combinations.
- **Rejected equivalences** suppress resolution but don't yet produce their own clarification.
- **No route `completed` state.** Completion evidence will need the planned database layer.

# Technical debt

- `backend/app/api/`, `backend/app/storage/`, `agent/` and `frontend/` are empty placeholders.
- No linter or CI is configured yet.
- The folder isn't a Git repository yet.

# Open questions

- STT provider (Groq Whisper) was proposed but not explicitly confirmed by the user.
- Deployment target for the backend (Render vs Fly) is undecided.
