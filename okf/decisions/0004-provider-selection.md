---
type: Decision Record
title: "0004: Domains, providers and budget"
description: User decisions on domains, language, timeline, LLM, STT and TTS providers, under a free-tier budget.
tags: [decision, providers, scope]
status: stable
decision_status: accepted
decided_on: 2026-11-08
generated: { by: copilot-sdk-agent/claude, at: "2026-11-08T17:39:00+05:30" }
sources:
  - id: plan
    resource: ../../PLAN.md
    title: Finalized build plan
---

# Decision

Chosen by the user on 2026-11-08:[^plan]

| Topic | Choice |
| --- | --- |
| Goal | Portfolio project, built as a complete app that handles every case type |
| Domains | Hospital discharge + cashless insurance (primary); corporate onboarding/offboarding (second) |
| Language | English only |
| Budget | Free tiers only |
| LLM | Groq `openai/gpt-oss-120b` and `openai/gpt-oss-20b` primary; OpenAI GPT-5.4 mini / GPT-5.4 / GPT-5 / GPT-5 mini as fallback |
| STT | Groq Whisper `whisper-large-v3-turbo` (proposed; not explicitly confirmed by the user) |
| TTS | Both Deepgram Aura and Cartesia |
| Timeline | One-week sprint |

# Consequences

- The OpenAI fallback isn't free; usage must stay low.
- Free-tier rate limits may affect live demos.
- Provider model availability must be rechecked when implementation starts.

[^plan]: Finalized build plan
