---
type: Decision Record
title: "0005: Deepgram and Cartesia for speech-to-text and text-to-speech"
description: Groq Whisper is dropped; Deepgram (primary) and Cartesia (alternate) provide both STT and TTS. Restates the remaining choices of 0004 unchanged.
tags: [decision, providers, voice, stt, tts]
status: stable
decision_status: accepted
decided_on: 2026-11-09
supersedes: 0004-provider-selection.md
generated: { by: claude-code/claude, at: "2026-11-09T03:30:00+00:00" }
sources:
  - id: plan
    resource: ../../PLAN.md
    title: Finalized build plan
---

# Context

[Decision 0004](0004-provider-selection.md) proposed Groq Whisper `whisper-large-v3-turbo` for speech-to-text, which the user had not confirmed. On 2026-11-09 the user decided Groq Whisper is not needed: Deepgram and Cartesia cover both directions of speech.

> The goal and timeline rows below were replaced on 2026-11-10 by [0006](0006-configurable-platform.md). The provider choices stand.

# Decision

| Topic | Choice |
| --- | --- |
| Goal | Portfolio project, built as a complete app that handles every case type |
| Domains | Hospital discharge + cashless insurance (primary); corporate onboarding/offboarding (second) |
| Language | English only |
| Budget | Free tiers only |
| LLM | Groq `openai/gpt-oss-120b` and `openai/gpt-oss-20b` primary; OpenAI GPT-5.4 mini / GPT-5.4 as paid fallback |
| STT | **Deepgram** streaming STT (primary) and **Cartesia** streaming STT (alternate/fallback), selectable per session |
| TTS | **Deepgram Aura** (primary) and **Cartesia** (alternate/fallback), selectable per session |
| Timeline | One-week sprint |

Groq stays only as the LLM provider. Both speech vendors are used through their LiveKit Agents plugins (`livekit-plugins-deepgram`, `livekit-plugins-cartesia`), so STT and TTS are each swappable by configuration.[^plan]

# Consequences

- Two speech vendor accounts and keys (Deepgram, Cartesia) cover the whole voice pipeline; no Groq audio usage.
- STT and TTS fallback can be the same vendor pair, simplifying the agent's provider-switching code.
- Free-tier limits of both vendors may constrain live demos; specific model ids (e.g. Deepgram Nova/Aura generations, Cartesia Ink/Sonic) must be rechecked when the voice agent is implemented (sprint day 5).
- The OpenAI fallback is still not free; usage must stay low.

Supersedes [0004](0004-provider-selection.md). Architecture: [system](/architecture/system.md).

[^plan]: Finalized build plan
