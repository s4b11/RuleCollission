---
type: Decision Record
title: "0003: Cloudflare R2 for file storage"
description: Evidence files, consented recordings and generated reports are stored in Cloudflare R2; Postgres holds only metadata.
tags: [decision, storage, r2]
status: stable
decision_status: accepted
decided_on: 2026-11-08
generated: { by: copilot-sdk-agent/claude, at: "2026-11-08T17:39:00+05:30" }
---

# Context

Cases need files that don't belong in a database: uploaded evidence (discharge summaries, pre-authorisation letters, TPA queries, bills, photos of instructions), recordings made with consent, and generated PDF reports. The user chose Cloudflare R2.

# Decision

Use Cloudflare R2 through its S3-compatible API (`boto3`). Prefixes: `evidence/{case_id}/`, `recordings/{case_id}/`, `reports/{case_id}/`. The browser uploads with presigned PUT URLs and downloads with short-lived presigned GET URLs. Postgres stores key, SHA-256, size, MIME type and verification status.

# Consequences

- Free tier (10 GB) is enough for the portfolio; R2 charges no egress fees.
- Local development can use any S3-compatible endpoint by changing the endpoint URL.
- Not implemented yet; see [system architecture](/architecture/system.md).
