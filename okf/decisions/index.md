# Decisions

* [0001 LLM proposes, engine and staff decide](0001-llm-proposes-engine-decides.md) - Model output never confirms requirements, approvals or routes
* [0002 Domain-agnostic rule packs](0002-domain-agnostic-rule-packs.md) - Domains are YAML rule packs consumed by one generic engine
* [0003 Cloudflare R2 for file storage](0003-cloudflare-r2-storage.md) - Evidence, recordings and reports live in R2; metadata in Postgres
* [0004 Domains, providers and budget](0004-provider-selection.md) - **Deprecated**, superseded by 0005
* [0005 Deepgram and Cartesia for STT and TTS](0005-deepgram-cartesia-speech.md) - Drops Groq Whisper; Deepgram + Cartesia for both speech directions; restates domains, Groq/OpenAI LLMs, free tiers
