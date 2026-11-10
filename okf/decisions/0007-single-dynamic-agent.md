---
type: Decision Record
title: "0007: One generic agent configured at session start"
description: A single LiveKit agent deployment serves every organisation; prompt, voice, tools and MCP servers come from the backend when a session starts.
tags: [decision, agent, livekit, tools]
status: stable
decision_status: accepted
decided_on: 2026-11-10
generated: { by: claude-code/claude, at: "2026-11-10T10:50:00+00:00" }
---

# Context

LiveKit Cloud's free plan allows one agent deployment. The user wants the prompt and tools changed from a dashboard without redeploying.

# Decision

- `agent/agent.py` holds only a fixed base prompt of safety rules (`agent/base_prompt.py`).
- At session start it calls `GET /internal/agent/sessions/{id}/config` and receives instructions, greeting, speech providers, tool definitions (name, description, JSON schema) and MCP servers.
- Each tool is registered from its schema and is the same proxy call to `POST /internal/agent/sessions/{id}/tools/{name}`. The backend runs the tool.
- Web sessions pass their session id in the agent dispatch metadata. Phone sessions are matched by the dialled number.

# Consequences

- Changing a prompt or enabling a tool is a database change that applies to the next session.
- The backend must be reachable when a session starts.
- The agent and backend share `AGENT_API_KEY`.
