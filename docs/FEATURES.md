# PulsePipe — Features

> Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

An itemized, source-backed tour of what PulsePipe can do.

## 1. Pipelines

A **pipeline** is a named event route: a list of transforms (`transform_spec`)
plus the subscriber endpoints it fans out to (`sinks`). Pipelines are the unit
of configuration and the dedup scope.

| Endpoint | Behavior |
|---|---|
| `POST /api/pipelines` | Create. Duplicate name → **409** (`ValueError` from `create_pipeline`) |
| `GET /api/pipelines` | List with `event_count` + `subscriber_count` |
| `GET /api/pipelines/{id}` | Single pipeline with counts |
| `GET /api/pipelines/by-name/{name}` | Lookup by unique name (404 if absent) |
| `PATCH /api/pipelines/{id}` | Patch `description`, `source`, `transform_spec`, `sinks` (404 if absent) |
| `DELETE /api/pipelines/{id}` | Delete — cascades to events, subscribers, alerts, rules (404 if absent) |

## 2. Subscribers

Subscribers are HTTP(S) endpoints registered on a pipeline; every emitted event
is `POST`ed to each subscriber's `endpoint` as a JSON payload.

| Endpoint | Behavior |
|---|---|
| `POST /api/pipelines/{pipeline_id}/subscribers` | Register a subscriber (404 on missing pipeline) |
| `GET /api/pipelines/{pipeline_id}/subscribers` | List a pipeline's subscribers |
| `DELETE /api/subscribers/{id}` | Remove (returns 204/404) |

Dispatch is POST-only with a per-call timeout (`PULSEPIPE_DISPATCH_TIMEOUT`,
default 2 s). Delivery is either **sync** (inside the request) or **async**
(background daemon thread), selected by `PULSEPIPE_DISPATCH_MODE`.

Useful for demos: `GET /api/echo` is a built-in subscriber sink that returns
200, so you can wire a pipeline to it and watch real end-to-end delivery.

## 3. Event transforms

An ordered set of deterministic, local operations — no network, no functions,
pure data munging applied to every payload in sequence:

- `tag:<keyword>` — add a tag (creates `payload.tags` list)
- `normalize:<field>` — lowercase + strip a string
- `extract:<field>:<alias>` — copy a field to an alias
- `pluck:<a.b.c>` — hoist a nested value to top level
- `drop:<field>` — remove a field
- `add:<field>:<literal>` — set a literal value

Unknown ops and missing-field references are skipped; ingestion never fails
because of a typo.

## 4. Event ingestion

`POST /api/events` with `{event_id?, pipeline, payload}`:

- **201** on success; returns the stored event plus per-subscriber `emit`
  outcomes.
- **404** if the pipeline does not exist.
- **Dedup** — sending the same `event_id` again (same pipeline) returns the
  stored event with `dedup: true` and does **not** re-dispatch.
- Omitting `event_id` auto-generates a UUIDv4.

## 5. Metrics (live)

All computed on demand from the event store:

| Endpoint | Returns |
|---|---|
| `GET /api/metrics/throughput?window_seconds=60` | `events`, `duration_seconds`, `events_per_second` |
| `GET /api/metrics/counts` | `total_events` + per-pipeline counts |
| `GET /api/metrics/latency` | `avg/max/min_latency_ms` over `received_at→emitted_at` |
| `GET /api/metrics/queue` | per-pipeline depth of `status='received'` events |

The dashboard polls these every 4 s.

## 6. Alerts

Two rule types, stored in `alert_rules`:

- **Keyword** — fires when an event payload contains `keyword`.
- **Threshold** — fires when ≥ N events arrive within `window_seconds`.

| Endpoint | Behavior |
|---|---|
| `POST /api/alert-rules` | Create (rule_type must be `keyword`/`threshold`; required field must be present else **422**; bad pipeline → **404**) |
| `GET /api/alert-rules` | List rules |
| `DELETE /api/alert-rules/{id}` | Remove (204/404) |
| `POST /api/alerts/evaluate` | Run all enabled rules now; returns `rules_evaluated`, `alerts_fired`, `alerts` |
| `GET /api/alerts?limit=50` | List fired alerts |

Rules may omit `pipeline_id` to apply across all pipelines.

## 7. Replay

`POST /api/replay` re-emits stored events. Exactly one selector:

| Selector | Meaning |
|---|---|
| `{"event_id": "..."}` | a single event |
| `{"window_from": ISO, "window_to": ISO}` | all events in a time range |
| `{"limit": N}` | the most recent N events (default 10, max 1000) |

Emitted events are delivered to the pipeline's subscribers **again**, and every
replay is recorded in `replay_log` (audit trail). Response:
`{requested, events_selected, deliveries, failures, replayed_at}`.

## 8. Seed / demo data

On first boot (`PULSEPIPE_SEED_ON_START=true` and an empty `pipelines` table),
`app/seed.py` creates:

- **3 pipelines** — `webhook-ingest`, `order-events`, `clickstream`, each with
  its own transforms and one `-echo` subscriber pointing at `/api/echo`.
- **2 alert rules** — a keyword rule `error-keyword` on clickstream and a
  threshold rule `order-spike` on order-events.
- **3 sample events** stored with `status='received'`.

`scripts/seed.py` is a standalone helper to reset and reseed any database file.

## 9. Dashboard

`frontend/index.html` is served at `/` — a dark, self-contained console showing
live cards (pipelines, total events, throughput, queue, latency, alerts), the
pipeline list, and the most recent events. No build tooling required.

## 10. Health & docs

- `GET /api/health` → `{status, app, version, database, time}` (runs a real
  `SELECT 1` on the DB).
- Swagger UI at `/api/docs`; raw schema at `/api/openapi.json`.