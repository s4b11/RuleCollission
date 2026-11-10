---
type: Decision Record
title: "0008: Realtime over LiveKit, dashboards by polling"
description: Voice, typed chat and transcripts travel through the LiveKit room (WebRTC); dashboards refresh with ordinary requests; the backend has no WebSocket endpoint.
tags: [decision, realtime, webrtc]
status: stable
decision_status: accepted
decided_on: 2026-11-10
generated: { by: claude-code/claude, at: "2026-11-10T10:50:00+00:00" }
---

# Decision

- The patient page joins a LiveKit room for audio, typed messages and live transcript.
- The patient page reads the case state, and dashboards read their lists, with plain requests repeated every few seconds.
- FastAPI exposes no WebSocket endpoint. This replaces the WebSocket channel in the earlier plan.

# Consequences

- One realtime technology to operate.
- Dashboard updates can lag by a few seconds.
