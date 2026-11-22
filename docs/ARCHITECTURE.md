# PulsePipe — Architecture

> Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

This document describes how PulsePipe is structured and how a single event
flows through the system, based directly on the source in `backend/`.

## 1. Big picture

PulsePipe is a **single FastAPI application** backed by one **SQLite file**.
There is no external broker, cache or queue. Pipelines live in SQL; events are
stored, transformed, dispatched synchronously (or from a background thread) to
subscriber HTTP endpoints; and observability (metrics, alerts, replay) is
derived **on request** from the stored event history.

```
   Producers ──POST /api/events──▶  PulsePipe (FastAPI)
   (webhooks, forms, CRMs)            │
                                      ├─ transforms   (services/transforms.py)
                                      ├─ store        (events table, dedup)
                                      ├─ dispatch     (services/events.py)
                                      │     └──▶ Subscriber HTTP endpoints
                                      └─ observe      (metrics / alerts / replay)
```

## 2. Layered modules

The code is split into four layers, all under `backend/`:

| Layer | Location | Responsibility |
|---|---|---|
| Entrypoint | `main.py` | `create_app()` factory; CORS, router wiring, static serving, first-boot seeding |
| HTTP layer | `app/routers/` | FastAPI routers; parse/validate requests, map services to HTTP, raise `HTTPException`s |
| Service layer | `app/services/` | Pure business logic and DB access — no HTTP knowledge |
| Storage | `app/database.py` | SQLite connection, schema DDL (`SCHEMA`), row/JSON helpers |
| Contracts | `app/schemas.py` | Pydantic request/response models for the wire API |
| Config | `app/config.py` | `Settings` object read from environment / `.env` |

### 2.1 Entrypoint — `backend/main.py`

- `create_app()` builds the `FastAPI` app with docs at `/api/docs` and
  OpenAPI at `/api/openapi.json`.
- CORS is wide open (`allow_origins=["*"]`) for local dashboards.
- Each router in `app/routers/` is included **under the `/api` prefix**.
- If `settings.seed_on_start` is true, the `lifespan` context manager calls
  `seed()` before the server starts serving.
- The pre-built dashboard `frontend/index.html` is **mounted at `/`** as static
  files (only if the directory exists).

### 2.2 Storage — `app/database.py`

A thread-safe wrapper (`Database`) around a single shared `sqlite3`
connection. Key design points:

- `SCHEMA` DDL creates 6 tables (see §6) with `PRAGMA foreign_keys = ON`.
- `connect()` is lazy and guarded by an `RLock`; `check_same_thread=False`
  lets concurrent request handlers share the one connection.
- `execute`/`executemany`/`query`/`query_one` are the DAO primitives.
- `dumps`/`loads` serialize/deserialize JSON `TEXT` columns (transforms,
  sinks, payloads, configs).
- `get_db()` returns a process-global singleton, constructed lazily from
  `settings.database_path` so importing modules never opens a connection.

### 2.3 Service layer — `app/services/`

Seven modules, each importing `Database`/`get_db` and taking an optional `db`
argument for testability:

- **`pipelines.py`** — CRUD for named pipelines, with aggregated
  `event_count` / `subscriber_count`. `create_pipeline` catches a SQLite
  unique-constraint error and re-raises `ValueError` (router → 409).
- **`subscribers.py`** — register/remove subscribers; `create_subscriber`
  raises `LookupError` on a missing pipeline (router → 404); cascading
  deletes via FK.
- **`transforms.py`** — pure, deterministic payload transforms (see §4). No DB.
- **`events.py`** — the ingest pipeline: lookup pipeline → dedup → deep-copy
  payload → apply transforms → store row → dispatch to subscribers. Also
  `list_events`, `get_event`, `dispatch_event`.
- **`metrics.py`** — live reads over the `events` table: throughput,
  counts, latency, queue depth.
- **`alerts.py`** — keyword and threshold rule evaluation, persisting fired
  alerts.
- **`replay.py`** — re-emit selected events, writing each to `replay_log`.

Every service function accepts `db: Optional[Database] = None` and falls back
to the global `get_db()`, which is what keeps unit tests hermetic.

### 2.4 HTTP layer — `app/routers/`

Eight routers, each exposing an `APIRouter`:

| Router file | Routes |
|---|---|
| `health.py` | `GET /api/health`, `GET /api/echo` |
| `pipelines.py` | `GET/POST /api/pipelines`, `GET/PATCH/DELETE /api/pipelines/{id}`, `GET /api/pipelines/by-name/{name}` |
| `subscribers.py` | `GET/POST /api/pipelines/{id}/subscribers`, `DELETE /api/subscribers/{id}` |
| `events.py` | `POST /api/events`, `GET /api/events`, `GET /api/events/{id}` |
| `metrics.py` | `GET /api/metrics/{throughput,counts,latency,queue}` |
| `alerts.py` | `GET/POST/DELETE /api/alert-rules`, `GET /api/alerts`, `POST /api/alerts/evaluate` |
| `replay.py` | `POST /api/replay` |

Error conventions: missing pipeline/subscriber → **404**; duplicate pipeline →
**409**; invalid rule config → **422**.

## 3. Request lifecycle — one event end to end

1. **Ingest** — `POST /api/events` with `{event_id?, pipeline, payload}`.
2. **Schema** — `EventIngest` validates; if `event_id` is omitted, a UUIDv4 is
   generated (pydantic `validate_default=True` + `field_validator`).
3. **Pipeline lookup** — `events.py` looks up the pipeline by name; unknown
   pipeline → `LookupError` → **404**.
4. **Dedup** — the service checks `(event_id, pipeline_id)` against the
   `events` table. On a hit, the stored event is returned with `dedup=true`
   and **no re-dispatch** occurs.
5. **Transform** — `apply_transforms(payload, pipeline.transform_spec)` returns
   a deep-copied, transformed payload plus the list of applied transforms
   (an unrecognized keyword is silently skipped and does not fail ingestion).
6. **Store** — a row is inserted with `status='received'` and `received_at`.
7. **Dispatch** — `dispatch_event` loads the pipeline's subscribers and POSTs
   the JSON payload to each:
   - `sync` mode: inline, within the request; `status` becomes `emitted` (any
     OK) or `failed` (all subscribers errored).
   - `async` mode: a daemon thread performs the POSTs so `POST /api/events`
     returns immediately with `status='received'`.
   Each delivery yields an `EmitResult {subscriber_id, name, endpoint, ok,
   detail}`; the API response carries them under `emit`, per
   `subscribers`-note in the router.
8. **Return** — the stored event (enriched with `emit` outcomes) is returned
   with **201**.

## 4. Transform key‏word language

Pipelines carry an ordered `transform_spec: list[str]`. Each entry is a
`op[:arg1[:arg2...]]` keyword applied to a **deep copy** of the payload:

| Keyword | Effect |
|---|---|
| `extract:<field>:<alias>` | Copy `payload[field]` → `payload[alias]` |
| `pluck:<a.b.c>` | Move a dotted-path value to top level (alias = last segment) |
| `drop:<field>` | Remove `payload[field]` |
| `tag:<keyword>` | Append keyword to `payload["tags"]` (creates the list) |
| `normalize:<field>` | Lowercase + strip a string field (no-op if not a string) |
| `add:<field>:<literal>` | Set `payload[field] = literal` |

Unknown operations and missing-field `extract`/`pluck` are skipped gracefully.

## 5. Metrics & alerts — how they are computed

All computed live, on demand, from the `events` table:

- **Throughput** — `GET /api/metrics/throughput?window_seconds=60`: events whose
  `received_at` falls inside the window, divided by window duration →
  `events_per_second`.
- **Counts** — total rows plus per-pipeline breakdown.
- **Latency** — for events with `emitted_at`, the `received_at → emitted_at`
  delta in milliseconds (avg/max/min).
- **Queue** — events with `status='received'` (received but not yet emitted)
  per pipeline.

**Alert rules** are stored in `alert_rules` with a JSON `config`:

- `keyword` — fires when any event payload contains `config["keyword"]`
  (searched via JSON string match).
- `threshold` — fires when ≥ `config["threshold"]` events arrived within
  `config["window_seconds"]`.

Evaluation is pull-based: `POST /api/alerts/evaluate` runs all **enabled** rules
for the window, writes matching events to the `alerts` table (with the matched
`event_ids`), and returns a `AlertEvaluateResponse`. Rules may omit
`pipeline_id` to apply to every pipeline.

## 6. Database schema

| Table | Key columns | Notes |
|---|---|---|
| `pipelines` | `id`, `name UNIQUE`, `description`, `source`, `transform_spec` (JSON), `sinks` (JSON), timestamps | aggregation target |
| `subscribers` | `id`, `pipeline_id FK`, `name`, `endpoint`, `created_at` | cascade-deletes with pipeline |
| `events` | `id`, `event_id`, `pipeline_id FK`, `payload` (JSON), `received_at`, `emitted_at`, `status`, `dedup` | dedup index on `(event_id, pipeline_id)` |
| `alert_rules` | `id`, `pipeline_id FK`, `name`, `rule_type` (`keyword`/`threshold`), `config` (JSON), `enabled` | CHECK constraint on type |
| `alerts` | `id`, `rule_id FK`, `pipeline_id`, `severity`, `message`, `event_ids` (JSON), `triggered_at` | fired-alert audit |
| `replay_log` | `id`, `pipeline_id`, `event_id`, `source`, `replayed_at` | replay audit trail |

## 7. Concurrency & correctness notes

- One shared SQLite connection guarded by an `RLock` — writes are serialized,
  reads interleave; `check_same_thread=False` for request-handler use.
- Dedup key is a composite `(event_id, pipeline_id)` with a dedicated index,
  so the "same event on different pipelines" case is handled correctly.
- Dispatch can be made genuinely non-blocking via `sync`/`async` only by config
  at boot; the code path is chosen once in `config.is_async_dispatch`.
- Payloads are stored as JSON text and never mutated in place — transforms
  operate on a `copy.deepcopy`.

## 8. Deployment notes

Because it is a single FastAPI app over a file DB, deployment is portable:
run it under `uvicorn` behind any proxy (see `docs/DEPLOYMENT.md`), mount
`data/` as a persistent volume, and set `PULSEPIPE_*` env vars to configure
port, DB path, dispatch mode and seeding.