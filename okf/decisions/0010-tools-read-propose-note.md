---
type: Decision Record
title: "0010: Tools read, propose and take notes; they never decide"
description: Agent tools of every kind can look up records, propose and write notes, but cannot record a staff decision; external tools and MCP servers are untrusted.
tags: [decision, tools, mcp, safety]
status: stable
decision_status: accepted
decided_on: 2026-11-10
generated: { by: claude-code/claude, at: "2026-11-10T10:50:00+00:00" }
---

# Decision

- Built-in tools: `identify_subject`, `open_case`, `get_case_status`, `lookup_rules`, `propose_requirement`, `propose_equivalence`, `list_open_questions`, `get_documents_on_file`, `add_case_note`, `search_knowledge`.
- No tool creates a `Decision`. Decisions come only from signed-in staff, and the engine checks their office and role ([0001](0001-llm-proposes-engine-decides.md)).
- Admin-defined web tools and MCP servers must use `https` and may not resolve to private or local addresses. Their results are returned to the model as data.
- Every tool call is stored in `ToolInvocation`.

# Consequences

- A compromised or misleading external tool cannot approve anything.
- Tool headers are stored in plain text for now ([known issues](/development/known-issues.md)).
