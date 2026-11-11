---
type: Decision Record
title: "0014: Backend on Modal and a deliberately simple stack"
description: The backend deploys to Modal; several planned pieces are replaced by simpler ones to keep the code easy to read.
tags: [decision, hosting, simplicity]
status: stable
decision_status: accepted
decided_on: 2026-11-10
generated: { by: claude-code/claude, at: "2026-11-10T10:50:00+00:00" }
---

# Decision

- Backend hosting: Modal (`backend/modal_app.py`), with one container kept warm so session start is not delayed (replaced by [0018](0018-modal-scale-to-zero.md): the backend now scales to zero). Database: Neon Postgres. Web app: any static host.
- Tables are created with SQLAlchemy `create_all`; there are no Alembic migrations yet. Local runs and tests use SQLite.
- File uploads pass through the backend, which stores them in Cloudflare R2 when configured or on local disk otherwise. This replaces the presigned-URL flow in [0003](0003-cloudflare-r2-storage.md).
- Passwords use PBKDF2 from the standard library; sessions use a signed JWT.
- Code style: small modules, plain functions, few comments.

# Consequences

- Schema changes on a live database need a manual step until migrations are added.
- Modal's filesystem is temporary, so production needs Postgres and R2.
