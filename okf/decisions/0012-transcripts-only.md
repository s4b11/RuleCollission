---
type: Decision Record
title: "0012: Transcripts only, no call recording"
description: Conversations are stored as text transcripts; audio is never recorded.
tags: [decision, privacy, transcripts]
status: stable
decision_status: accepted
decided_on: 2026-11-10
generated: { by: claude-code/claude, at: "2026-11-10T10:50:00+00:00" }
---

# Decision

The agent posts each finished utterance to the backend, stored as `TranscriptLine`. No audio is recorded or stored.

# Consequences

- The `recordings/` storage prefix in [0003](0003-cloudflare-r2-storage.md) is not used.
- Staff read transcripts on the Conversations page and on each case.
