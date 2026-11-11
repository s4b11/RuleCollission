# RuleCollision

A voice and text assistant for people stuck between offices that each ask for the other's document first. It works out whether the person is really stuck, and ends every case with a route to follow, one question for the right office, or a clear report that a decision is needed.

Any organisation can configure it. The demo is a **fictional** hospital (Sunrise General); a second fictional company (Northwind Labs) shows that nothing is hospital-specific.

> The AI proposes; the rule engine and signed-in staff decide. No tool can record a decision.

## What is in this repository

| Folder | What it is |
| --- | --- |
| `backend/` | FastAPI app: rule engine, cases, staff decisions, agent settings, tool gateway, document search, rule drafting |
| `agent/` | The single LiveKit agent. It has no organisation knowledge; it fetches its prompt, voice, tools and MCP servers from the backend when a session starts |
| `frontend/` | React app: patient assistant, staff dashboard, Agent Studio |
| `rulepacks/` | The rule files for the two demo organisations |
| `okf/` | Project knowledge: architecture, features, decisions, known issues. Start at [`okf/index.md`](okf/index.md) |

## Run it locally

```bash
# 1. Backend (uses a local SQLite file and seeds the demo data)
cd backend
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/uvicorn app.main:app --port 8000

# 2. Web app
cd frontend
npm install && npm run dev        # http://localhost:5173

# 3. Agent (needs LiveKit, Deepgram, Cartesia and Groq keys in agent/.env)
cd agent
pip install -r requirements.txt
python agent.py dev
```

Sign in at `http://localhost:5173/login` with a demo account. Locally the password is `demo1234`; on a deployed server it is the `DEMO_PASSWORD` secret. Every office has a sign-in; the main ones:

| Account | Role |
| --- | --- |
| `admin@sunrise.example` | Hospital administrator (can open Agent Studio) |
| `billing@sunrise.example` | Billing approver |
| `tpa@sunrise.example` | Insurance (TPA) approver |
| `doctor@sunrise.example` | Treating doctor |
| `ward@sunrise.example` | Ward nurse (cannot approve exceptions) |
| `admin@northwind.example` | Northwind HR administrator (can open Agent Studio) |
| `it@northwind.example` | Northwind IT approver |
| `legal@northwind.example` | Northwind Legal approver |
| `finance@northwind.example` | Northwind Payroll approver |

The full list is in `backend/app/seed/demo.py`.

Patient pages: `http://localhost:5173/a/sunrise-discharge` and `http://localhost:5173/a/northwind-people`. A demo patient: admission number `SGH-2026-0412`, year of birth `1958`. On `/case`, try code `SGH424` with `SGH-2026-0424`, or `NW1051` with `NW-1051`.

Without provider keys, everything except live conversations and AI rule drafting works.

## Checks

```bash
cd backend && .venv/bin/python -m pytest -q      # engine and API tests
backend/.venv/bin/python scripts/check_okf.py     # knowledge bundle
cd frontend && npm run build                      # type-check and build
```

## Deploy

Deployment runs in GitHub Actions, so no key is ever stored in the repository. The workflow is [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml).

1. Create accounts: Modal, LiveKit Cloud, Neon (Postgres), Deepgram, Groq and Cloudflare.
2. In the repository, open **Settings → Secrets and variables → Actions** and add:

   | Secrets (required) | Where it comes from |
   | --- | --- |
   | `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET` | Modal → Settings → API tokens |
   | `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` | LiveKit Cloud → Settings → Keys |
   | `DATABASE_URL` | Neon connection string |
   | `JWT_SECRET`, `AGENT_API_KEY` | Two long random strings you make up |
   | `DEMO_PASSWORD` | Password for the demo accounts |
   | `DEEPGRAM_API_KEY`, `GROQ_API_KEY` | Deepgram and Groq consoles |
   | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` | Cloudflare (token with Account → Cloudflare Pages → Edit) |

   Optional secrets: `CARTESIA_API_KEY`, `OPENAI_API_KEY`, `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`.

   No addresses need to be entered: the workflow reads the Cloudflare Pages address and the Modal address itself and shows both in the run summary. Set the variable `BACKEND_URL` only if you later deploy the agent or web app on its own.

3. Open **Actions → Deploy → Run workflow**. Choose `all`, or one part.
4. The first agent run creates the agent and commits `agent/livekit.toml` (ids only, no secrets).
5. **Phone:** in LiveKit Cloud, get a phone number and add a dispatch rule that sends calls to the agent named `rulecollision`. Enter the number in Agent Studio → QR codes and phone. Calls end after 3 minutes.

All data in this repository is fictional. Never commit real patient, employee or institution data, or any keys.
