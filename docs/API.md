# PulsePipe — API Reference

> Base URL: `http://localhost:8000` — every API route is under `/api`.
> Interactive docs: Swagger UI at `/api/docs`, raw OpenAPI at `/api/openapi.json`.
> The dashboard is served at `/`.

Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

Routes live in `backend/app/routers/`; wire models are the Pydantic schemas in
`backend/app/schemas.py`. Business logic is in `backend/app/services/`.

## Conventions

- Responses are bare JSON objects/arrays (no envelope wrapper).
- Status codes: `200` reads/actions, `201` creates, `204` deletes,
  `404` unknown resource, `409` duplicate pipeline name, `422` validation /
  missing rule parameter.
- Timestamps are ISO-8601 UTC strings (`...Z` on responses produced by the
  API; SQLite `YYYY-MM-DD HH:MM:SS` on rows read back).

## Endpoint summary

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Health incl. DB reachability |
| POST | `/api/echo` | Echo body back (test sink for subscribers) |
| GET | `/api/pipelines` | List pipelines (+ event/subscriber counts) |
| POST | `/api/pipelines` | Create pipeline (201, 409 on dup name) |
| GET | `/api/pipelines/by-name/{name}` | Look up by unique name |
| GET | `/api/pipelines/{id}` | Get one pipeline |
| PATCH | `/api/pipelines/{id}` | Partial update |
| DELETE | `/api/pipelines/{id}` | Delete (cascades; 204) |
| GET | `/api/pipelines/{id}/subscribers` | List subscribers |
| POST | `/api/pipelines/{id}/subscribers` | Register subscriber (201, 404 pipeline) |
| DELETE | `/api/subscribers/{id}` | Remove subscriber (204) |
| POST | `/api/events` | Ingest event (201; dedup on `event_id`; 404 unknown pipeline) |
| GET | `/api/events?pipeline_id=&limit=50` | List stored events, newest first |
| GET | `/api/events/{id}` | Get one event by row id |
| GET | `/api/metrics/throughput?window_seconds=60` | Events/sec over window |
| GET | `/api/metrics/counts` | Total + per-pipeline counts |
| GET | `/api/metrics/latency` | Receive→emit latency stats (ms) |
| GET | `/api/metrics/queue` | Received-but-not-emitted depth per pipeline |
| GET | `/api/alert-rules` | List alert rules |
| POST | `/api/alert-rules` | Create rule (keyword \| threshold) |
| DELETE | `/api/alert-rules/{id}` | Delete rule |
| POST | `/api/alerts/evaluate` | Evaluate all enabled rules now |
| GET | `/api/alerts?limit=50` | Fired alerts, newest first |
| POST | `/api/replay` | Re-emit selected stored events |

---

## Health & echo — `routers/health.py`

### `GET /api/health`
```json
{"status": "ok", "app": "PulsePipe", "version": "1.0.0", "database": "ok", "time": "2026-11-15T10:00:00Z"}
```
`database` is `"unavailable"` if the SQLite probe fails — probe this from
load balancers / Uptime Kuma.

### `POST /api/echo`
Returns `{"received": <body>, "pulsepipe": "PulsePipe"}` with 200. Used as a
no-op subscriber endpoint by the seeded demo pipelines.

---

## Pipelines — `routers/pipelines.py`

### `POST /api/pipelines` → 201 (409 duplicate name)
```json
{
  "name": "webhooks",
  "description": "Inbound product webhooks",
  "source": "webhook",
  "transform_spec": ["drop-debug", "enrich-geo"],
  "sinks": ["https://hooks.example.com/pulse"]
}
```
`PipelineCreate`: `name` (1–120 chars, unique), `description`, `source`,
`transform_spec` (ordered keyword rules applied at ingest — see
`services/transforms.py`), `sinks` (subscriber endpoint URLs).

### `GET /api/pipelines`
```json
[{"id": 1, "name": "webhooks", "description": "...", "source": "webhook",
  "transform_spec": ["drop-debug"], "sinks": ["..."],
  "created_at": "...", "updated_at": "...", "event_count": 42, "subscriber_count": 2}]
```

### `GET /api/pipelines/{id}` · `GET /api/pipelines/by-name/{name}`
Single `PipelineOut`; 404 if missing.

### `PATCH /api/pipelines/{id}`
`PipelineUpdate` — any of `description`, `source`, `transform_spec`, `sinks`;
only sent fields change. 404 if missing.

### `DELETE /api/pipelines/{id}` → 204
Cascades to its events, subscribers and alert rules. 404 if missing.

---

## Subscribers — `routers/subscribers.py`

### `POST /api/pipelines/{id}/subscribers` → 201 (404 unknown pipeline)
```json
{"name": "dashboard-hook", "endpoint": "http://localhost:8000/api/echo"}
```
Returns `SubscriberOut`: `{id, pipeline_id, name, endpoint, created_at}`.

### `GET /api/pipelines/{id}/subscribers`
### `DELETE /api/subscribers/{id}` → 204 (404 if missing)

---

## Events — `routers/events.py`, `services/events.py`

### `POST /api/events` → 201 (404 unknown pipeline)
```json
{"event_id": "order-1234", "pipeline": "webhooks", "payload": {"type": "order.created", "amount": 99}}
```
`EventIngest`: `pipeline` (name, required), `payload` (JSON object),
`event_id` (optional client dedup key; a UUID is generated if omitted).

Behaviour: the pipeline's `transform_spec` rules are applied to the payload,
the event is stored with `received_at`, then dispatched to every subscriber
(sync inline by default, or on a background worker when
`PULSEPIPE_DISPATCH_MODE=async`). Re-posting the same `event_id` to the same
pipeline returns the stored event with `"dedup": true` and does **not**
dispatch again.

Response `EventOut`:
```json
{
  "id": 7, "event_id": "order-1234", "pipeline_id": 1, "pipeline": "webhooks",
  "payload": {"type": "order.created", "amount": 99},
  "received_at": "2026-11-15T10:00:01Z", "emitted_at": "2026-11-15T10:00:01Z",
  "status": "emitted", "dedup": false,
  "emit": [{"subscriber_id": 1, "subscriber_name": "dashboard-hook",
            "endpoint": "http://localhost:8000/api/echo", "ok": true, "detail": "200"}]
}
```

```bash
curl -s -X POST http://localhost:8000/api/events -H 'Content-Type: application/json' \
  -d '{"pipeline":"demo","event_id":"e1","payload":{"n":1}}' | jq .
```

### `GET /api/events?pipeline_id=1&limit=50`
List stored events newest first (`limit` 1–1000, default 50).

### `GET /api/events/{id}`
Single event by **row id** (not `event_id`); 404 if missing.

---

## Metrics — `routers/metrics.py`, `services/metrics.py`

| Endpoint | Response |
|----------|----------|
| `GET /api/metrics/throughput?window_seconds=60` | `{"window_seconds":60,"duration_seconds":58.2,"events":120,"events_per_second":2.06}` |
| `GET /api/metrics/counts` | `{"total_events":120,"pipelines":[{"pipeline_id":1,"pipeline":"webhooks","events":120}]}` |
| `GET /api/metrics/latency` | `{"emitted_events":118,"avg_latency_ms":3.1,"max_latency_ms":41.0,"min_latency_ms":0.8,"sample_period":"..."}` |
| `GET /api/metrics/queue` | `{"total_depth":2,"by_pipeline":[{"pipeline_id":1,"pipeline":"webhooks","events":2}]}` |

`window_seconds` is clamped to 1–86400. Queue depth = received-but-not-yet-emitted.

---

## Alerts — `routers/alerts.py`, `services/alerts.py`

### `POST /api/alert-rules` → 201
```json
{"pipeline_id": 1, "name": "spike", "rule_type": "threshold",
 "threshold": 100, "window_seconds": 60, "severity": "critical", "enabled": true}
```
```json
{"name": "contains-error", "rule_type": "keyword", "keyword": "error", "severity": "warning"}
```
- `rule_type`: `threshold` (fires when ≥ `threshold` events arrive within
  `window_seconds`, 1–86400, default 60) or `keyword` (fires when a payload
  contains `keyword`). 422 if the matching parameter is missing.
- `pipeline_id` optional (null = all pipelines); 404 if it references a
  missing pipeline. `severity`: `info|warning|critical`.

### `GET /api/alert-rules`
`AlertRuleOut[]`: `{id, pipeline_id, pipeline, name, rule_type, config, enabled, created_at}`.

### `POST /api/alerts/evaluate`
Evaluates every enabled rule against stored events and persists fired alerts:
```json
{"rules_evaluated": 3, "alerts_fired": 1,
 "alerts": [{"id": 1, "rule_id": 2, "pipeline_id": 1, "pipeline": "webhooks",
             "severity": "critical", "message": "...", "event_ids": ["e1","e2"],
             "triggered_at": "..."}]}
```

### `GET /api/alerts?limit=50`
Fired alerts newest first (`AlertOut[]` as above).

### `DELETE /api/alert-rules/{id}`
Deletes the rule (its fired alerts remain for audit).

---

## Replay — `routers/replay.py`, `services/replay.py`

### `POST /api/replay`
Re-emit stored events to their pipeline's subscribers. Exactly one selector:
`event_id` (single event), `window_from`/`window_to` (ISO-8601 range), or
`limit` (most recent N; default 10, max 1000).

```json
{"event_id": "order-1234"}
{"window_from": "2026-11-15T00:00:00Z", "window_to": "2026-11-16T00:00:00Z"}
{"limit": 25}
```

Response:
```json
{"requested": "limit=25", "events_selected": 25, "deliveries": 48, "failures": 0, "replayed_at": "..."}
```

---

## Errors

| Code | When | Body |
|------|------|------|
| 404 | Unknown pipeline (ingest/subscriber/alert rule), pipeline id, event id, subscriber id | `{"detail": "pipeline 'x' not found"}` |
| 409 | Duplicate pipeline name | `{"detail": "pipeline 'x' already exists"}` |
| 422 | Schema violation, or keyword/threshold rule missing its parameter | `{"detail": "..."}` |

## See also

- `docs/RUNNING.md` — run commands and curl recipes
- `docs/ARCHITECTURE.md` — ingestion → transform → dispatch → observe flow
- `docs/env-config.md` — `PULSEPIPE_*` variables (dispatch mode/timeout, DB path…)
