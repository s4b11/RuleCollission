# Decisions

* [0001 LLM proposes, engine and staff decide](0001-llm-proposes-engine-decides.md) - Model output never confirms requirements, approvals or routes
* [0002 Domain-agnostic rule packs](0002-domain-agnostic-rule-packs.md) - Domains are YAML rule packs consumed by one generic engine
* [0003 Cloudflare R2 for file storage](0003-cloudflare-r2-storage.md) - Evidence, recordings and reports live in R2; metadata in Postgres
* [0004 Domains, providers and budget](0004-provider-selection.md) - **Deprecated**, superseded by 0005
* [0005 Deepgram and Cartesia for STT and TTS](0005-deepgram-cartesia-speech.md) - Drops Groq Whisper; Deepgram + Cartesia for both speech directions; restates domains, Groq/OpenAI LLMs, free tiers
* [0006 Configurable platform with a hospital showcase](0006-configurable-platform.md) - Multi-organisation platform; hospital demo; phases replace the sprint
* [0007 One generic agent configured at session start](0007-single-dynamic-agent.md) - Prompt, voice, tools and MCP come from the backend per session
* [0008 Realtime over LiveKit, dashboards by polling](0008-webrtc-and-polling.md) - WebRTC for conversations; no application WebSockets
* [0009 Document search explains; the engine decides](0009-rag-explains-engine-decides.md) - Knowledge search with citations; vectors in the main database
* [0010 Tools read, propose and take notes](0010-tools-read-propose-note.md) - No tool records a decision; external tools and MCP are untrusted
* [0011 Phone line, 3-minute calls and identification](0011-phone-and-identification.md) - LiveKit telephony, call cap, configurable identifier, case code, QR codes
* [0012 Transcripts only](0012-transcripts-only.md) - No audio recording
* [0013 AI drafts rules; staff approve them](0013-ai-rule-drafts.md) - Drafts from documents or chat become rules only after approval
* [0014 Backend on Modal and a simple stack](0014-modal-hosting-and-simple-stack.md) - Modal, Neon, no migrations yet, uploads through the backend
* [0015 Plain dashboard design](0015-plain-dashboard-design.md) - **Deprecated**, superseded by 0017
* [0016 Deploy with a manual GitHub Actions workflow](0016-deploy-with-github-actions.md) - Modal, LiveKit Cloud and Cloudflare Pages from one workflow; keys as GitHub secrets
* [0017 Polished dashboard design](0017-polished-dashboard-design.md) - Icons, bundled font, soft shadows, dark sidebar; still no neon or gradients
* [0018 Backend scales to zero on Modal](0018-modal-scale-to-zero.md) - No always-on container; stops after 1.5 idle minutes; normal spinners while it starts
