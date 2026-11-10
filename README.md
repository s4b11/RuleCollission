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

Sign in at `http://localhost:5173/login` with a demo account, password `demo1234`:

| Account | Role |
| --- | --- |
| `admin@sunrise.example` | Hospital administrator (can open Agent Studio) |
| `billing@sunrise.example` | Billing approver |
| `tpa@sunrise.example` | Insurance (TPA) approver |
| `ward@sunrise.example` | Ward nurse (cannot approve exceptions) |
| `admin@northwind.example` | The second organisation |

The patient page is `http://localhost:5173/a/sunrise-discharge`. A demo patient: admission number `SGH-2026-0412`, year of birth `1958`.

Without provider keys, everything except live conversations and AI rule drafting works.

## Checks

```bash
cd backend && .venv/bin/python -m pytest -q      # engine and API tests
backend/.venv/bin/python scripts/check_okf.py     # knowledge bundle
cd frontend && npm run build                      # type-check and build
```

## Deploy

1. **Database:** create a Neon Postgres database and copy its connection string.
2. **Backend on Modal:** create a Modal secret named `rulecollision` with the backend values from [`.env.example`](.env.example), then `cd backend && modal deploy modal_app.py`.
3. **Agent on LiveKit Cloud:** `cd agent && lk agent create`, and add the agent values from `.env.example` as secrets. Only one agent deployment is needed; every organisation shares it.
4. **Phone:** in LiveKit Cloud, get a phone number and add a dispatch rule that sends calls to the agent named `rulecollision`. Enter the number in Agent Studio → QR codes and phone. Calls end after 3 minutes.
5. **Web app:** build `frontend/` with `VITE_API_URL` set and host the `dist/` folder (for example on Cloudflare Pages).

All data in this repository is fictional. Never commit real patient, employee or institution data, or any keys.
