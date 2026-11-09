# AGENTS.md — RuleCollision

Instructions for any AI coding agent working in this repository. Project knowledge lives in the OKF v0.2 bundle at [`okf/`](okf/index.md).

## 1. Start every task here

1. Read [`okf/index.md`](okf/index.md) and [`okf/current-state.md`](okf/current-state.md).
2. Follow links only to the concepts relevant to the task (architecture, features, decisions, development). Do not load the whole bundle.
3. Open the actual source files and tests before relying on any knowledge claim. Code and tests are the evidence for implemented behavior; [`details.md`](details.md) and [`PLAN.md`](PLAN.md) are the authority for intended behavior.
4. Identify applicable decisions in [`okf/decisions/`](okf/decisions/index.md) and respect them. Superseding a decision requires a new decision record.
5. Keep the scope of changes to the requested task.

Distinguish **implemented**, **intended**, **proposed** and **historical** behavior. Never present one as another.

## 2. Project rules

- **The LLM proposes; the deterministic engine and authenticated staff decide.** Never let model output confirm a requirement, approve an alternative or mark a route confirmed. See [decision 0001](okf/decisions/0001-llm-proposes-engine-decides.md).
- Domain behavior belongs in rule packs (`rulepacks/*.yaml`), not in engine code. See [decision 0002](okf/decisions/0002-domain-agnostic-rule-packs.md).
- Every rule, hospital, insurer, TPA and company in rule packs and tests is **fictional**. Never add real patient, employee or institutional data.
- Never commit secrets. Provider keys (Groq, OpenAI, Deepgram, Cartesia, LiveKit, Cloudflare R2, Neon) belong in an uncommitted `.env` only.

## 3. Build and test

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest -q
```

Validate the knowledge bundle (uses PyYAML from the backend venv):

```powershell
backend\.venv\Scripts\python scripts\check_okf.py
```

Every engine change needs a golden test in `backend/tests/` covering the case type it affects.

## 4. While working

- Record significant changes to interfaces, behavior, architecture, data models, dependencies or operations as you make them.
- Record newly discovered issues, constraints and consequential decisions.
- If a knowledge document is wrong and you have established the correct facts, fix it.
- For long or interrupted work, write a concise checkpoint to [`okf/current-state.md`](okf/current-state.md) and the affected concept.
- Do not rewrite indexes or the log for incidental edits.

## 5. Verification

- Run the checks for the changed area (pytest, `scripts/check_okf.py`, and later lint/build).
- Report exactly which checks ran and their results, including failures.
- Never claim a test, verification or human review that did not happen. Only add OKF `verified` entries for checks that actually ran; use `human:<id>` only with human confirmation.

## 6. Knowledge synchronization (part of finishing any meaningful task)

1. Update the affected feature or architecture concepts and their `generated` metadata.
2. Add or revise a decision record for consequential technical choices; mark superseded ones `status: deprecated` and link the replacement.
3. Update [`okf/current-state.md`](okf/current-state.md) if status, active work, blockers, risks or next actions changed.
4. Update [`okf/development/`](okf/development/index.md) for issues, debt and planned work.
5. Add a dated entry (newest first, `## YYYY-MM-DD`) to [`okf/log.md`](okf/log.md).
6. Refresh the relevant `index.md` when documents are added, renamed, moved or deprecated.
7. Run `scripts/check_okf.py`.

Writing rules: short, factual, structured Markdown; link instead of duplicating; no transcripts, hidden reasoning, secrets or personal data. Concept documents need YAML frontmatter with a non-empty `type`; `index.md` and `log.md` are reserved and carry no frontmatter (except `okf_version` on the root index). Actors use `<producer>/<version>`, `human:<id>` or `process:<id>`; timestamps are ISO 8601 with an explicit offset.

## 7. Handover

End each task by stating: what changed, which checks ran and their results, which knowledge documents changed, what remains incomplete/blocked/unverified, and useful next actions. Never present an interrupted checkpoint as a completed task.

## 8. Git and parallel work

This folder is not yet a Git repository. Once it is, keep `okf/` in the same repository as the code. Treat `okf/current-state.md`, `okf/index.md` and `okf/log.md` as shared integration points: reconcile them against the merged implementation, and never describe unmerged branch work as repository-wide state. Do not commit, push or merge without authorization.
