# PulsePipe

> Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

**PulsePipe** is a real-time event-streaming and observability engine built on
FastAPI. It lets you define **named pipelines**, transform inbound JSON events,
dispatch them to **subscribers** (any HTTP endpoint), and observe the whole
flow through live **metrics**, **alerts** and **replay** — with no external
infrastructure beyond a single SQLite file.

Designed as the "AI SDR Outbound Engine" backbone: producer services (webhooks,
forms, CRMs) push events to PulsePipe, transforms enrich/normalize them,
subscribers push them on to downstream consumers, and operators watch
throughput, detect anomalies and replay any event.

---

## Highlights

- **Pipeline-centric** — create pipelines with an ordered `transform_spec` and
  a set of subscriber endpoints.
- **Deterministic transforms** — apply `tag:`, `normalize:`, `extract:`,
  `drop:`, `add:`, `pluck:` keywords in order to every payload.
- **At-least-once ingestion with dedup** — repeated `event_id` sends are
  detected per pipeline and never re-dispatched.
- **Two dispatch modes** — `sync` (deliver inside the request) or `async`
  (deliver on a background thread, non-blocking ingest).
- **Live metrics** — throughput (events/sec), counts, receive→emit latency, and
  queue depth, computed on demand from the event store.
- **Alerts** — keyword rules (payload contains a string) and volume-threshold
  rules, evaluated on demand and persisted.
- **Replay** — re-emit a single event, a time window, or the most recent N, with
  a full audit log.
- **Self-contained** — the included static dashboard (`frontend/index.html`)
  renders the console at `/`, and seed data makes first boot instantly usable.

---

## Quick start

Requires **Python 3.11+** (developed on 3.14).

```bash
cd PulsePipe

# 1. Create a virtual environment and install
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements-dev.txt

# 2. Start the API + dashboard
cd backend
./.venv/Scripts/python main.py
# or: ./venv/Scripts/uvicorn main:app --reload
```

Open <http://localhost:8000/> for the dashboard and
<http://localhost:8000/api/docs> for interactive API docs (Swagger).

On first boot the server **seeds demo data** (3 pipelines, 2 alert rules,
3 events) so the dashboard has something to show immediately.

### Try the full flow

```bash
# Create a pipeline that normalizes email and tags events as "live"
curl -s -X POST localhost:8000/api/pipelines \
  -H 'Content-Type: application/json' \
  -d '{"name":"demo","transform_spec":["normalize:email","tag:live"]}'

# Subscribe it to the app's own echo endpoint (returns 200)
curl -s -X POST localhost:8000/api/pipelines/1/subscribers \
  -H 'Content-Type: application/json' \
  -d '{"name":"echo","endpoint":"http://127.0.0.1:8000/api/echo"}'

# Ingest an event — it is transformed, stored & delivered to the subscriber
curl -s -X POST localhost:8000/api/events \
  -H 'Content-Type: application/json' \
  -d '{"pipeline":"demo","payload":{"email":"  ALICE@Example.com "}}'
# → payload.email becomes "alice@example.com", tags=["live"], status="emitted"
```

---

## Repository layout

```
PulsePipe/
├── README.md
├── .gitignore
├── backend/
│   ├── main.py                 # FastAPI app factory + entrypoint
│   ├── app/
│   │   ├── config.py           # env-driven runtime settings
│   │   ├── database.py         # SQLite storage layer (schema + DAO)
│   │   ├── schemas.py          # Pydantic request/response models
│   │   ├── seed.py             # first-boot demo data
│   │   ├── routers/            # HTTP layer (8 routers under /api)
│   │   └── services/           # business logic (7 service modules)
│   ├── tests/                  # pytest suite (27 tests)
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/
│   └── index.html              # static console (served at /)
├── scripts/
│   └── seed.py                 # standalone DB reseed helper
└── docs/                       # architecture, stack, features, run, deploy
```

See **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** for how the modules fit
together, **[docs/INSTALLATION.md](docs/INSTALLATION.md)** for prerequisites and
setup, **[docs/RUNNING.md](docs/RUNNING.md)** for full run/test instructions,
**[docs/API.md](docs/API.md)** for every endpoint (also live at `/api/docs`),
**[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** for local/Docker/VPS deployment
(Coolify + Caddy + Uptime Kuma), plus
**[docs/FEATURES.md](docs/FEATURES.md)**, **[docs/TECH-STACK.md](docs/TECH-STACK.md)**,
**[docs/CODEBASE-ORGANIZATION.md](docs/CODEBASE-ORGANIZATION.md)**,
**[docs/env-config.md](docs/env-config.md)** and
**[docs/PLAYBOOK-CROSSWALK.md](docs/PLAYBOOK-CROSSWALK.md)**.

---

## Tests

```bash
cd backend
./.venv/Scripts/python -m pytest -q
# → 27 passed
```

The suite spins up an in-process HTTP echo server so event delivery is tested
end-to-end without any external network.

---

## Configuration

All runtime settings come from environment variables (optionally via a
`backend/.env` file). See **[docs/RUNNING.md](docs/RUNNING.md#configuration)**
for the full table.

| Variable | Default | Purpose |
|---|---|---|
| `PULSEPIPE_DB_PATH` | `data/pulsepipe.db` | SQLite database file |
| `PULSEPIPE_SEED_ON_START` | `true` | Seed demo data on first boot |
| `PULSEPIPE_DISPATCH_MODE` | `sync` | `sync` or `async` emission |
| `PULSEPIPE_DISPATCH_TIMEOUT` | `2.0` | seconds to wait per subscriber |
| `PULSEPIPE_PORT` / `PULSEPIPE_HOST` | `8000` / `0.0.0.0` | bind address |

---

## Roadmap

- Webhook receivers and enrichment/ICP-scoring transforms (playbook FR-P1/P3/P4 hooks).
- Sequence engine on top of dispatch mode/timeout (FR-P5).
- Named channel subscribers: e-mail with warm-up + caps, LinkedIn, CRM sync (FR-P3/P6).
- Reply classification and Cal.com booking (FR-P4/P5); weekly copy evals (FR-P9).
- Auth on the API (open by design for the demo today).

## License

Internal project. Seed data and demo endpoints are for local development only.