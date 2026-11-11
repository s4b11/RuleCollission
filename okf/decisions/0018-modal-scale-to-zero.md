---
type: Decision Record
title: "0018: Backend scales to zero on Modal"
description: No always-on Modal container; the backend starts on the first request and stops after 5 idle minutes, and the web app shows its normal loading spinners meanwhile.
tags: [decision, operations, hosting, cost]
status: stable
decision_status: accepted
decided_on: 2026-11-11
generated: { by: claude-code/claude, at: "2026-11-11T12:00:00+00:00" }
---

# Context

The user has a monthly Modal allowance of 30 USD and asked for no minimum instance. [0014](0014-modal-hosting-and-simple-stack.md) kept one container warm.

# Decision

- `backend/modal_app.py`: no `min_containers`; `scaledown_window=300`, so a container stops after 5 minutes without requests.
- The embedding model (`BAAI/bge-small-en-v1.5`) is downloaded into the image at build time (`FASTEMBED_CACHE_PATH=/models`), so a cold start does not download it.
- During a cold start the web app shows only its normal spinners and "Loading…"; no extra message (user preference).

# Consequences

- Idle cost is close to zero; the first request after a quiet spell is slower (expected seconds, not measured yet).
- An open dashboard polls every 8–15 seconds and so keeps the container running while the tab is open.
- Replaces the warm-container part of [0014](0014-modal-hosting-and-simple-stack.md); the rest of 0014 stands.
