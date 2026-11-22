# PulsePipe — Running Locally

> Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

Everything you need to install, configure, run, and test PulsePipe on a
development machine or CI.

## 1. Prerequisites

- **Python 3.11+** (developed/tested on 3.14.9).
- No other services are required — PulsePipe uses a file-based SQLite DB and
  its own in-process dispatch.

## 2. Installation

```bash
cd PulsePipe

# Create a virtual environment (paths below use the Windows layout;
# on macOS/Linux replace Scripts/python with bin/python)
python -m venv backend/.venv

# Install runtime + dev/test dependencies
backend/.venv/Scripts/python -m pip install --upgrade pip
backend/.venv/Scripts/python -m pip install -r backend/requirements-dev.txt
```

`requirements-dev.txt` includes `pytest` on top of the runtime deps in
`requirements.txt`.

## 3. Running the server

```bash
cd backend
./.venv/Scripts/python main.py
```

or, equivalently:

```bash
cd backend
./.venv/Scripts/uvicorn main:app --reload
```

On first boot the app **seeds demo data** (3 pipelines, 2 alert rules, 3
events) and prints a log line like:

```
INFO:app.seed:seeded 3 pipelines, 2 alert rules, 3 demo events
```

The seed is idempotent: it only runs when the `pipelines` table is empty. To
reset the DB to the demo state, delete `data/pulsepipe.db` (or run
`../scripts/seed.py`) and restart.

### What is served

| URL | Content |
|---|---|
| `http://localhost:8000/` | Static dashboard (`frontend/index.html`) |
| `http://localhost:8000/api/docs` | Swagger UI |
| `http://localhost:8000/api/health` | Health probe |
| `http://localhost:8000/api/openapi.json` | Raw OpenAPI schema |

## 4. Configuration

All settings are read from environment variables; an optional `backend/.env`
file is loaded first (key/value or `KEY=value`, `KEY="value"` forms) but does
**not** override already-set environment variables.

| Variable | Default | Description |
|---|---|---|
| `PULSEPIPE_NAME` | `PulsePipe` | App display name (shown in health & docs) |
| `PULSEPIPE_VERSION` | `1.0.0` | Version string (health response) |
| `PULSEPIPE_HOST` | `0.0.0.0` | Bind host |
| `PULSEPIPE_PORT` | `8000` | Bind port |
| `PULSEPIPE_DEBUG` | `false` | `uvicorn --reload` when `python main.py` |
| `PULSEPIPE_DB_PATH` | `data/pulsepipe.db` | SQLite file (parent dir created if absent) |
| `PULSEPIPE_SEED_ON_START` | `true` | Seed demo data when pipelines table is empty |
| `PULSEPIPE_DISPATCH_MODE` | `sync` | `sync` or `async`/`background` emission |
| `PULSEPIPE_DISPATCH_TIMEOUT` | `2.0` | seconds to wait per subscriber before giving up |

`PULSEPIPE_DISPATCH_MODE` matters for latency vs. consistency:

- **`sync`** — subscriber POSTs happen inside the `POST /api/events` request;
  the response reports the real `status` (`emitted`/`failed`) and per-subscriber
  `emit` outcomes. Deterministic, good for testing.
- **`async` / `background`** — emission happens on a daemon worker thread; the
  ingest request returns immediately and the event's status stays `received`
  until a worker finishes it. Non-blocking, good for high-throughput ingest.

## 5. End-to-end smoke test

Once the server is up, try the full lifecycle:

```bash
# 1. Create a pipeline with transforms
curl -s -X POST localhost:8000/api/pipelines -H 'Content-Type: application/json' \
  -d '{"name":"demo","transform_spec":["normalize:email","tag:live"]}' | jq

# 2. Subscribe it to the built-in echo sink (id 4 = your "demo" pipeline)
curl -s -X POST localhost:8000/api/pipelines/4/subscribers -H 'Content-Type: application/json' \
  -d '{"name":"echo","endpoint":"http://127.0.0.1:8000/api/echo"}'

# 3. Ingest an event
curl -s -X POST localhost:8000/api/events -H 'Content-Type: application/json' \
  -d '{"pipeline":"demo","payload":{"email":"  ADA@Example.com ","tier":"enterprise"}}'
# → payload.email becomes "ada@example.com", tags=["live"], status="emitted",
#   emit[0].ok == true  (delivered to the echo endpoint)

# 4. Observe
curl -s localhost:8000/api/metrics/counts | jq
curl -s "localhost:8000/api/metrics/throughput?window_seconds=3600" | jq
```

> Tip for step 2: pipeline IDs are sequential from 1; get the right one with
> `curl -s localhost:8000/api/pipelines/by-name/demo | jq .id`.

## 6. Replay demo data

The seeded events are stored with `status='received'`, so they can be replayed:

```bash
curl -s -X POST localhost:8000/api/replay -H 'Content-Type: application/json' \
  -d '{"event_id":"demo-webhook-001"}'
# → {"requested":"event_id=demo-webhook-001","events_selected":1,"deliveries":1,"failures":0,...}
```

## 7. Running the tests

```bash
cd backend
./.venv/Scripts/python -m pytest -q
# → 27 passed
```

The suite uses FastAPI's `TestClient` and starts an **in-process HTTP echo
server** so delivery is exercised end-to-end with no external network. Tests
redirect the DB to a throwaway temp file and disable seeding & async dispatch
(`tests/conftest.py`); an autouse fixture wipes the `events`/`alerts` tables
between tests.

Coverage of areas (all under `backend/tests/`):

| File | Covers |
|---|---|
| `test_pipelines.py` | create/list/get/by-name, 409 dup, PATCH, DELETE, 404s |
| `test_subscribers.py` | add/list/delete, counts, 404s |
| `test_events.py` | transforms, dedup, list/get, emit success & failure |
| `test_metrics.py` | health, empty + populated counts/throughput/queue/latency |
| `test_alerts.py` | keyword & threshold firing, no-fire, validation, delete |
| `test_replay.py` | by event_id, by limit, unknown event |

## 8. Resetting the database

```bash
# Delete the file and restart (reseed happens on boot):
rm -f data/pulsepipe.db

# Or use the standalone helper (works while a DB exists):
python scripts/seed.py                    # reseed default DB
python scripts/seed.py --path data/demo.db
```

`scripts/seed.py` deletes the target file and re-runs `app.seed.seed()`, so the
DB is guaranteed to be empty-by-start.

## 9. Troubleshooting

- **`Unable to run tests` / `No module named 'app'`** — run pytest from inside
  `backend/` (the `app` package and `main.py` are importable from there).
- **Demo events show as `received` forever** — that is by design (see seed
  docstring); dispatch them on demand via `/api/replay` once the server runs.
- **Subscriber POSTs failing (status `failed`)** — the endpoint is unreachable
  or taken longer than `PULSEPIPE_DISPATCH_TIMEOUT`. Point subscribers at
  `/api/echo` on the same host for a reliably-successful sink.
- **WinError 10048 / "address already in use"** — another app holds
  `PULSEPIPE_PORT`; change it via `PULSEPIPE_PORT`.