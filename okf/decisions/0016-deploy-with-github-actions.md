---
type: Decision Record
title: "0016: Deploy with a manual GitHub Actions workflow"
description: One manually started workflow deploys the backend to Modal, the agent to LiveKit Cloud and the web app to Cloudflare Pages, with every key held as a GitHub secret.
tags: [decision, deployment, ci]
status: stable
decision_status: accepted
decided_on: 2026-11-10
generated: { by: claude-code/claude, at: "2026-11-10T11:25:00+00:00" }
sources:
  - id: workflow
    resource: ../../.github/workflows/deploy.yml
    title: Deploy workflow
---

# Context

Deploy tools need secret keys on the machine that runs them. Keys must not be stored in the repository or in a development session.

# Decision

- `.github/workflows/deploy.yml` is started by hand and deploys `all`, `backend`, `agent` or `web`.[^workflow]
- **Backend:** writes the Modal secret `rulecollision` from GitHub secrets, runs `modal deploy`, then checks `/health` when `BACKEND_URL` is set.
- **Agent:** uses LiveKit's `livekit/deploy-action`. The first run creates the agent and commits `agent/livekit.toml`; later runs deploy a new version.
- **Web app:** builds with `VITE_API_URL` and publishes to the Cloudflare Pages project `rulecollision`. `frontend/public/_redirects` sends every path to the app.
- The workflow discovers both addresses: it creates the Pages project and reads its address from the Cloudflare API, and reads the Modal address from the deploy output. The `BACKEND_URL` variable is only a fallback when the agent or web app is deployed alone.

# Consequences

- Deployment is not automatic on push.
- The workflow must be on the default branch before GitHub offers the "Run workflow" button.
- The first agent run pushes a commit, which a protected branch would reject.
- Extends [0014](0014-modal-hosting-and-simple-stack.md).

[^workflow]: Deploy workflow
