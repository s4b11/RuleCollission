# RuleCollision update log

## 2026-11-10
* **Update**: First deploy succeeded (Modal, LiveKit Cloud, Cloudflare Pages); live use not yet confirmed. See [current state](/current-state.md).
* **Decision**: [0017](/decisions/0017-polished-dashboard-design.md) redesigns the web app; [0015](/decisions/0015-plain-dashboard-design.md) deprecated.
* **Update**: The deploy workflow now discovers the web and backend addresses itself ([0016](/decisions/0016-deploy-with-github-actions.md)).
* **Decision**: [0016](/decisions/0016-deploy-with-github-actions.md) deploys backend, agent and web app from one manual GitHub Actions workflow.
* **Decision**: Recorded [0006](/decisions/0006-configurable-platform.md) through [0015](/decisions/0015-plain-dashboard-design.md): configurable platform, single dynamic agent, WebRTC and polling, knowledge search, tool limits, phone and identification, transcripts only, AI rule drafts, Modal hosting, plain design.
* **Creation**: Platform backend (`backend/app/`), single LiveKit agent (`agent/`) and web app (`frontend/`). See [system architecture](/architecture/system.md) and [platform features](/features/platform.md).
* **Update**: `PLAN.md` rewritten as v2; the one-week sprint became [build phases](/development/sprint-plan.md).
* **Update**: [Known issues](/development/known-issues.md) now lists unverified areas and platform limitations.

## 2026-11-09
* **Decision**: [0005](/decisions/0005-deepgram-cartesia-speech.md) drops Groq Whisper; Deepgram and Cartesia provide both STT and TTS. [0004](/decisions/0004-provider-selection.md) deprecated. `PLAN.md` updated to match.
* **Creation**: Proposed [engine limitation resolutions](/development/engine-limitations.md); recorded a newly found issue (equivalences not office-scoped) in [known issues](/development/known-issues.md).
* **Update**: Corrected stale statements: the project is a Git repository, and the `api/`, `storage/`, `agent/`, `frontend/` placeholders do not exist yet.

## 2026-11-08
* **Initialization**: Set up the OKF v0.2 knowledge bundle, [AGENTS.md](../AGENTS.md) and `scripts/check_okf.py`.
* **Creation**: Implemented the deterministic [rule engine](/architecture/rule-engine.md) with 30 passing golden tests.
* **Creation**: Added the `hospital_discharge` and `corporate_lifecycle` [rule packs](/features/rule-packs.md) (fictional).
* **Decision**: Recorded decisions [0001](/decisions/0001-llm-proposes-engine-decides.md) through [0004](/decisions/0004-provider-selection.md).
* **Creation**: Finalized scope and stack in `PLAN.md` from the concept in `details.md`.
