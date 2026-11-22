# PulsePipe — Installation

Step-by-step setup from a clean machine to a running PulsePipe instance.

> Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ recommended (3.10 works; code uses `X \| None` / `dict[str, Any]`) | `python --version` |
| pip | bundled with Python | `python -m pip install -U pip` |
| Disk | ~50 MB | venv + SQLite file under `data/` |
| OS | Windows / macOS / Linux | both Windows and POSIX commands shown |

No database server, no broker, no API keys — PulsePipe is self-contained
(SQLite + in-process dispatch).

## 1. Get the code

```bash
git clone <repo-url> PulsePipe
cd PulsePipe
```

## 2. Create a virtual environment (in `backend/`)

The app is always run from `backend/` so that `main:app` and `app.*` are
importable:

```bash
cd backend

# Windows (cmd)
python -m venv .venv
.venv\Scripts\activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt          # app + pytest
# or, for development:
pip install -r requirements-dev.txt      # -r requirements.txt + pytest>=8,<10
```

`requirements.txt`:

| Package | Purpose |
|---------|---------|
| `fastapi>=0.115,<1` | Web framework / routing / validation |
| `uvicorn[standard]>=0.30,<1` | ASGI server |
| `pydantic>=2.7,<3` | Request/response schemas (`app/schemas.py`) |
| `httpx>=0.27,<1` | Subscriber dispatch + test client |
| `pytest>=8,<10` | Tests (`requirements-dev.txt` adds it explicitly) |

## 4. Configure environment (optional)

```bash
cp .env.example .env     # then edit values — see docs/env-config.md
```

`backend/app/config.py` loads `backend/.env` at import time (simple
`KEY=value` parser, no python-dotenv dependency); variables already present
in the process environment always win. Defaults work for local dev:

| Var | Default |
|-----|---------|
| `PULSEPIPE_DB_PATH` | `<project root>/data/pulsepipe.db` |
| `PULSEPIPE_PORT` | `8000` |
| `PULSEPIPE_SEED_ON_START` | `true` |
| `PULSEPIPE_DISPATCH_MODE` | `sync` |

## 5. Database setup

Nothing to do manually. On startup the lifespan hook in `backend/main.py`
opens the SQLite DB (`app/database.py` creates the `pipelines`, `subscribers`,
`events`, `alert_rules`, `alerts` tables idempotently) and, when
`PULSEPIPE_SEED_ON_START=true`, seeds demo pipelines/events/rules
(`app/seed.py`). `scripts/seed.py` can re-seed manually.

## 6. First run

```bash
cd backend
uvicorn main:app --reload --port 8000
# or: python main.py   (uses PULSEPIPE_HOST/PULSEPIPE_PORT, --reload if PULSEPIPE_DEBUG=true)
```

Then open:

- Dashboard: http://localhost:8000/
- Swagger UI: http://localhost:8000/api/docs
- OpenAPI JSON: http://localhost:8000/api/openapi.json
- Health: http://localhost:8000/api/health

## 7. Verify the install

```bash
curl -s http://localhost:8000/api/health
# {"status":"ok","app":"PulsePipe","version":"1.0.0","database":"ok","time":"..."}

curl -s -X POST http://localhost:8000/api/events -H 'Content-Type: application/json' \
  -d '{"pipeline":"demo","event_id":"smoke-1","payload":{"hello":"world"}}'

curl -s "http://localhost:8000/api/metrics/counts"
```

## 8. Run the tests

```bash
cd backend
python -m pytest -q        # when a tests/ directory is present
```

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `ModuleNotFoundError: main` / `app` | Run from `backend/`, not the repo root. |
| `address already in use` | Use `--port 8001` or change `PULSEPIPE_PORT`. |
| `pipeline 'x' not found` on ingest | Create it first: `POST /api/pipelines` (or wait for the seed). |
| Subscriber deliveries failing (`ok:false`) | Endpoint URL unreachable from the server; `POST /api/echo` is the built-in test sink. |
| DB file in unexpected place | `PULSEPIPE_DB_PATH` is relative to CWD; default is `<root>/data/pulsepipe.db`. |

## Next steps

- `docs/RUNNING.md` — run commands, env vars, curl recipes
- `docs/API.md` — full REST reference
- `docs/ARCHITECTURE.md` — ingestion → transform → dispatch → observe flow
- `docs/DEPLOYMENT.md` — production/VPS deployment
