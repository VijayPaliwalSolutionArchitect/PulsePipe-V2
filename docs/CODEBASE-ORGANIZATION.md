# PulsePipe — Codebase Organization

> Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

A guided tour of every source file, where things live, and the conventions to
follow when extending the project.

## Directory tree

```
PulsePipe/
├── README.md
├── .gitignore
├── backend/
│   ├── main.py                     # FastAPI app factory + uvicorn entry
│   ├── requirements.txt            # runtime deps
│   ├── requirements-dev.txt        # runtime + pytest
│   ├── app/
│   │   ├── __init__.py             # package marker
│   │   ├── config.py               # Settings: env-driven runtime config
│   │   ├── database.py             # Database class: SQLite schema + DAO
│   │   ├── schemas.py              # all Pydantic request/response models
│   │   ├── seed.py                 # first-boot demo data
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── health.py           # /api/health, /api/echo
│   │   │   ├── pipelines.py        # pipeline CRUD + by-name
│   │   │   ├── subscribers.py      # subscriber CRUD
│   │   │   ├── events.py           # ingest, list, get
│   │   │   ├── metrics.py          # throughput/counts/latency/queue
│   │   │   ├── alerts.py           # rules + evaluate + list
│   │   │   └── replay.py           # replay
│   │   └── services/
│   │       ├── __init__.py         # exports service names
│   │       ├── pipelines.py        # pipeline CRUD logic
│   │       ├── subscribers.py      # subscriber registration
│   │       ├── transforms.py       # pure payload transforms
│   │       ├── events.py           # ingest/dedup/dispatch + event read
│   │       ├── metrics.py          # live metric computations
│   │       ├── alerts.py           # rule eval + alert persistence
│   │       └── replay.py           # replay + audit log
│   └── tests/
│       ├── conftest.py             # temp DB, echo server, TestClient
│       ├── test_pipelines.py
│       ├── test_subscribers.py
│       ├── test_events.py
│       ├── test_metrics.py
│       ├── test_alerts.py
│       └── test_replay.py
├── frontend/
│   └── index.html                  # static dashboard (served at /)
├── scripts/
│   └── seed.py                     # standalone DB reset + reseed
└── docs/                           # this documentation set
```

## Per-file explanation

### Entry point — `backend/main.py`

- `create_app()` — the single constructor: adds CORS, mounts every router under
  `/api`, wires the `lifespan` (seed on boot), and serves `frontend/` at `/`.
- `app = create_app()` — module-level instance for `uvicorn main:app`.
- `__main__` block — convenience `python main.py` runner.

### `app/config.py`

`Settings` reads each value from the environment (with an optional `backend/.env`
loaded first and never overriding real env vars). Publishes `settings`
singleton. Owns the `database_path` (auto-creates `data/`), seed flag, dispatch
mode/timeout, and frontend dir. `is_async_dispatch` derives from
`dispatch_mode`.

### `app/database.py`

- `SCHEMA` — DDL for the six tables.
- `Database` — thread-safe wrapper: lazy shared connection (`RLock`,
  `check_same_thread=False`, `foreign_keys=ON`), DAO methods `execute`,
  `executemany`, `query`, `query_one`, and `dumps`/`loads` for JSON columns.
- `get_db()` — returns a process-global, lazily-constructed instance from
  `settings.database_path`.

### `app/schemas.py`

Every Pydantic model in one place. Groups: health, pipeline, subscriber, event
(`EventIngest`, `EventOut`, `EmitResult`), metrics, alerts (`AlertRuleCreate`,
`AlertOut`, `AlertEvaluateResponse`), replay. `EventIngest` uses
`ConfigDict(validate_default=True)` + a `field_validator` so omitted
`event_id` becomes a generated UUID.

### `app/seed.py`

`seed(db=None) -> bool` — guards on an empty `pipelines` table, creates three
demo pipelines (each with a `-echo` subscriber on `/api/echo`), two alert rules,
and inserts three sample events **directly** into `events` (status
`received`). Direct insert (not via `ingest`) avoids dispatching to our own
not-yet-listening socket during startup.

### `app/routers/`

Thin HTTP layer. Conventions:

- Each module defines a module-level `router = APIRouter()`.
- Domain errors map to status codes: `LookupError` → 404, `ValueError`
  (duplicate) → 409, `KeyError`/validation → 422.
- DB is obtained per-call via `get_db()` injected into service calls.
- `events.py` attachs a `emit` list of per-subscriber `EmitResult`s to the
  ingest response for observability.

### `app/services/`

Business logic, no HTTP coupling. Every public function accepts
`db: Database | None = None` for test injection.

- **`pipelines.py`** — CRUD with aggregated counts; `UNIQUE constraint` →
  `ValueError` → 409.
- **`subscribers.py`** — registration; FK failure → `LookupError` → 404;
  `all_subscribers()` joins pipeline names for cross-pipeline work.
- **`transforms.py`** — pure `apply_transforms(payload, rules) -> (payload,
  applied)`. Operates on a deep copy; unknown ops are skipped; never throws on
  a bad rule.
- **`events.py`** — `ingest` (lookup → dedup → transform → store → dispatch,
  returns `(stored, results, is_dedup)`), `dispatch_event` (httpx POST per
  subscriber with `PULSEPIPE_DISPATCH_TIMEOUT`), `list_events`, `get_event`.
- **`metrics.py`** — on-demand `throughput`, `counts`, `latency`, `queue`.
- **`alerts.py`** — `create_rule`, `list_rules`, `delete_rule`, `evaluate_rules`
  (keyword & threshold), `list_alerts`.
- **`replay.py`** — `replay(data)` with exactly one selector, writes every
  replay to `replay_log`.

### `tests/`

One file per feature area plus `conftest.py` (temp DB, disabled seed, in-process
echo server fixture, TestClient, per-test table wipe). Run from `backend/`:

```bash
./.venv/Scripts/python -m pytest -q
```

### `frontend/index.html`

A single self-contained HTML/CSS/JS dashboard. Calls `/api/*` with `fetch`
every 4 s and renders live cards, the pipeline list, and recent events. No
build step.

### `scripts/seed.py`

Standalone CLI: deletes the target DB and reseeds. Useful for demos and
resetting a dev store.

## Conventions & how to extend

1. **Add an endpoint** — define/reuse a Pydantic model in `schemas.py`, add a
   service function in `services/<topic>.py`, wire a route in
   `routers/<topic>.py`, register the router in `main.py`.
2. **Service functions always take `db`** — default to `get_db()` but accept
   injection for tests.
3. **Error contract** — map logic failures to `LookupError` (404) or
   `ValueError` (409) in services; the routers translate.
4. **Every transform is additive and safe** — never mutate the input payload;
   guard against missing fields.
5. **Tests live beside features** — add to the matching `test_*.py`; use the
   `client` and `echo_server` fixtures. Keep them DB-hermetic.
6. **No new hard dependencies** — stay on stdlib where a `sqlite3`/`json`/
   `threading` approach already exists.
7. **Respect layering** — routers must not run business logic; services must
   not know about FastAPI; `database.py` is the only place that touches SQLite
   SQL (beyond the schema strings in `SCHEMA`).