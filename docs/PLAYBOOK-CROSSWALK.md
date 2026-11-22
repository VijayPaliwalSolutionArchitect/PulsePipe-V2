# PulsePipe — Playbook Crosswalk

How this repository maps to **Project 5 — "AI SDR / Outbound Engine"** of the
JARVIS AI Portfolio Playbook (see the product note in `README.md`: PulsePipe
is the event backbone companion to ScoutForge). The chapter excerpt available
to this repo covers the shared platform sections **§4.4–4.8** (Tables 36–38:
what you build / work breakdown, deliverables, benefits, VPS deployment,
portfolio) and the project chapter **§5.1–5.3** (Table 39 at a glance, demand,
Table 40 architecture, Table 41 personas, Table 42 MoSCoW, Table 43
FR-P1…P9, NFRs, KPIs). The deployment/portfolio steps are tracked in
`docs/DEPLOYMENT.md` → §9 and in the last table below.

> Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

Legend: ✅ implemented · 🟡 partial · ⬜ planned

## §5.1 Snapshot

| Playbook item | Status | Evidence / note |
|---------------|--------|-----------------|
| One-liner: real-time event pipeline that ingests, transforms, routes and observes streams | ✅ | FastAPI description in `backend/main.py` |
| Solo, ~8 weeks, $0 infra | ✅ | single process + SQLite, no external services |
| Hero-project tier (deployed, monitored, documented) | 🟡 | docs/tests in repo; live deploy flow in `docs/DEPLOYMENT.md` |

## §5.2 Demand signals → addressed by

| Signal (playbook) | Addressed by | Status |
|-------------------|--------------|--------|
| Reps lose hours to manual admin/list hygiene | Automatable ingest + dedup + routing | ✅ `POST /api/events`, `event_id` dedup |
| Data scattered across tools, no single stream | Named pipelines as the single routing unit | ✅ `pipelines` + `services/pipelines.py` |
| No real-time visibility into what is happening | Metrics + alerts + replay | ✅ `/api/metrics/*`, `/api/alerts`, `/api/replay`, dashboard |

## §5.2 Reference architecture (Table 40, 5 playbook layers → repo mapping)

| Playbook layer | Playbook role | In this repo | Status |
|----------------|---------------|--------------|--------|
| 1. Ingestion | Webhooks/APIs/queues | `POST /api/events` (REST); webhook receivers ⬜ | 🟡 |
| 2. Normalization | Schema, dedup | `event_id` dedup, `transform_spec` rules (`services/transforms.py`) | ✅ |
| 3. Routing | Fan-out to consumers | Named pipelines → subscribers (`services/events.py`, `services/subscribers.py`) | ✅ |
| 4. Scoring/Enrichment | AI scoring of leads | ⬜ planned (transform hooks are the extension point) |
| 5. Orchestration | Sequences, throttling | Dispatch mode sync/async + per-subscriber timeout (`PULSEPIPE_DISPATCH_MODE/TIMEOUT`); full sequences ⬜ | 🟡 |
| 6. Delivery | Send via channels | HTTP subscriber dispatch (POST to endpoint URLs) — email/SMS/CRM channels ⬜ | 🟡 |
| Observability (steps 4–5 of the flow) | Metrics, alerts, replay | `/api/metrics/*`, alert rules + evaluate, `/api/replay`, dashboard | ✅ |

Flow steps 1–5 in the chapter (ingest → normalize → route → score → deliver)
map to `services/events.py::ingest` → `services/transforms.py` → pipeline
lookup → subscriber dispatch → `services/metrics.py` + `services/alerts.py`.

## §5.3 PRD — MoSCoW (Table 42)

- **Must**: event ingest API, pipelines, subscribers, dispatch, metrics,
  health → all ✅ (see `docs/API.md`).
- **Should**: alert rules (keyword/threshold), replay, dashboard → ✅.
- **Could**: enrichment/scoring hooks (FR-P3/P4), sequences (FR-P5), reply
  tracking (FR-P7) → ⬜.
- **Won't (this phase)**: multi-tenant SaaS, auth → ⬜ by design.

## §5.3 Functional requirements (FR-P1 … FR-P9, Table 43)

| FR | Requirement | Status | Evidence |
|----|-------------|--------|----------|
| FR-P1 | Ingest leads/events via API/webhooks | 🟡 REST ✅ (`POST /api/events`); webhook receiver ⬜ |
| FR-P2 | Normalize & dedupe incoming events | ✅ `event_id` dedup + `transform_spec` (`services/events.py`, `services/transforms.py`) |
| FR-P3 | Enrich with firmographic data | ⬜ extension point via transform rules |
| FR-P4 | AI scoring of events/leads | ⬜ planned on top of pipelines |
| FR-P5 | Multi-step sequences | ⬜ dispatch mode/timeout is the primitive |
| FR-P6 | Send via channels (email/LinkedIn/webhook) | 🟡 generic HTTP subscriber dispatch ✅; named channels ⬜ |
| FR-P7 | Track replies/opens | ⬜ |
| FR-P8 | Analytics dashboard | ✅ `/api/metrics/throughput|counts|latency|queue` + `frontend/` dashboard |
| FR-P9 | Alerting & observability | ✅ `/api/alert-rules`, `/api/alerts/evaluate`, `/api/health` |

## §5.3 NFRs

| NFR | Status | Note |
|-----|--------|------|
| Ingest latency low (sync mode) | ✅ | inline dispatch, `PULSEPIPE_DISPATCH_TIMEOUT` caps waiting; `async` mode offloads |
| No event loss on crash | 🟡 | events are stored before dispatch; in-flight async emits can be replayed via `/api/replay` |
| Observability | ✅ | 4 metrics endpoints + health + alerts |
| Security | 🟡 | CORS wide open (`*`) for the demo dashboard — restrict `allow_origins` in prod; no auth yet ⬜ |
| Maintainability | ✅ | routers → services → SQLite layering; Pydantic schemas separate from storage |

## §5.4–5.8 (work breakdown / deliverables / benefits / deployment / portfolio)

| Item | Status | Where |
|------|--------|-------|
| Sprint breakdown | 🟡 core sprints landed (ingest, pipelines, dispatch, metrics, alerts, replay, dashboard) | this repo |
| Deliverables: app, docs, API reference, tests, live URL + monitor | 🟡 local ✅, docs ✅ (`docs/`), API ✅ (`docs/API.md` + `/api/docs`), live URL via deployment flow | `docs/DEPLOYMENT.md` platform section (Coolify + Caddy `pulse.shivamitcs.com` + Uptime Kuma + nightly backup) |
| Benefits/KPIs | ✅ measurable via `/api/metrics/*` (throughput, latency, queue depth) |
| Portfolio angle | `README.md` product note — companion event backbone to ScoutForge's outbound engine |
