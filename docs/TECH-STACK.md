# PulsePipe — Technology Stack

> Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

## Runtime & language

| Component | Version | Notes |
|---|---|---|
| Python | 3.14.9 (requires 3.11+) | Best-effort `from __future__ import annotations` keeps it modern; pydantic v2 needs 3.9+ |
| OS | Windows 11 (dev); cross-platform | pure-Python, no platform-specific deps |

## Backend dependencies

Installed via `backend/requirements.txt`. The exact versions present in the
project venv (`backend/.venv`) at the time of writing:

| Package | Installed | Requirement | Role |
|---|---|---|---|
| **FastAPI** | 0.162.4 | `>=0.115,<1` | web framework, routing, validation, docs |
| **Starlette** | 1.10.0 | — (FastAPI dependency) | ASGI runtime layer, `TestClient`, static files |
| **Uvicorn** | 0.54.0 | `>=0.30,<1` | ASGI server / entrypoint |
| **Pydantic** | 2.14.3 | `>=2.7,<3` | schema models, validation, serialization |
| **httpx** | 0.28.1 | `>=0.27,<1` | outbound POSTs to subscribers |
| **pytest** | 9.2.0 | `>=8,<10` (dev) | test runner |
| **python-dotenv** | optional | not pinned | `.env` loading (`config.py` degrades gracefully if absent) |

`backend/requirements-dev.txt` also includes `pytest`.

### Standard library (no extra deps)

Almost the entire storage layer is stdlib:

- `sqlite3` — persistence (single file DB, `PRAGMA foreign_keys = ON`)
- `json` — payload/column serialization
- `threading` — shared-connection lock + async dispatch threads
- `http.server`/`socketserver` — in-process echo subscriber used by the test suite
- `uuid`, `datetime`, `pathlib`, `contextlib`, `logging`, `os`

## Frontend

| Component | Notes |
|---|---|
| Dashboard | `frontend/index.html` — a single self-contained HTML+CSS+JS page (no build step, no npm) |
| API access | vanilla `fetch()` calls the `/api/*` endpoints on the same origin |
| Refresh | auto-polls every 4 seconds for live metrics |

The frontend **has no package.json / node_modules** — it is plain static files
served by FastAPI at `/`. There is deliberately nothing to install.

## Interfaces

| Interface | Location |
|---|---|
| Interactive API docs | `http://localhost:8000/api/docs` (Swagger UI) |
| OpenAPI schema | `/api/openapi.json` |
| Health probe | `GET /api/health` |
| Dashboard | `/` |

## Why this stack

- **Single process, zero ops** — FastAPI over SQLite means one container / one
  process, trivial to run locally and in CI.
- **Deterministic & auditable** — all transforms are pure functions; every
  ingest, delivery and replay is persisted, so the event store doubles as the
  source of truth for metrics and alerts.
- **No auth built in (by design)** — PulsePipe is intended to sit behind a
  gateway / service mesh; CORS is open for the local dashboard.