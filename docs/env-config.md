# PulsePipe — Environment Configuration

> Version: v0.1 · 15-11-26 · Author: SHIVAM ITCS (JARVIS)

All runtime config is read from `PULSEPIPE_*` environment variables by
`backend/app/config.py` at import time. An optional `backend/.env` file is
loaded if present (simple `KEY=value` parser — **no python-dotenv
dependency**): comments (`#`) and blank lines are skipped, quotes are
stripped, and a key **already set in the process environment always wins**.
Placeholders live in `backend/.env.example`. Never commit real values.

## Variables

| Variable | Default | Type / parsing | Purpose |
|----------|---------|----------------|---------|
| `PULSEPIPE_NAME` | `PulsePipe` | str | App name — FastAPI title, `/api/health`, `/api/echo` |
| `PULSEPIPE_VERSION` | `1.0.0` | str | Version reported by the API |
| `PULSEPIPE_HOST` | `0.0.0.0` | str | Bind host for `python main.py` |
| `PULSEPIPE_PORT` | `8000` | int | Bind port for `python main.py` (uvicorn `--port` overrides) |
| `PULSEPIPE_DEBUG` | `false` | bool: `1/true/yes/on` | Enables uvicorn `--reload` when run via `python main.py` |
| `PULSEPIPE_DB_PATH` | `<project root>/data/pulsepipe.db` | path | SQLite file; parent dir is auto-created. Use an absolute path on persistent storage in production |
| `PULSEPIPE_SEED_ON_START` | `true` | bool | Seed demo pipelines/events/rules on first boot (only when tables are empty) |
| `PULSEPIPE_DISPATCH_MODE` | `sync` | `sync` \| `async`/`background` | `sync`: emit to subscribers inline within the ingest request (deterministic). `async`: emit on a background worker thread (non-blocking ingest) |
| `PULSEPIPE_DISPATCH_TIMEOUT` | `2.0` | float seconds | Per-subscriber HTTP timeout during dispatch |

Not env-configurable: the dashboard directory is fixed at `<project root>/frontend`
(`settings.frontend_dir`), mounted at `/` if it exists.

There are **no secrets** in PulsePipe — no API keys or tokens are required.
If any are ever introduced, keep them in the environment only and redact them
from docs (`[REDACTED]`).

## Setting variables

```bash
# backend/.env (loaded automatically at import)
PULSEPIPE_PORT=8000
PULSEPIPE_DB_PATH=/var/lib/pulsepipe/pulsepipe.db
PULSEPIPE_DISPATCH_MODE=async

# or process environment (macOS/Linux)
export PULSEPIPE_DB_PATH=/var/lib/pulsepipe/pulsepipe.db
cd backend && uvicorn main:app --port 8000

# Windows cmd / PowerShell
set PULSEPIPE_PORT=8000
$env:PULSEPIPE_PORT="8000"

# Docker / Coolify
# ENV PULSEPIPE_DB_PATH=/data/pulsepipe.db  + persistent volume on /data
```

## Notes

- Values are read **once at import** — change them before starting the process.
- Relative `PULSEPIPE_DB_PATH` resolves against the process working directory
  (`backend/` in all documented commands). Use absolute paths in production.
- The DB file is runtime state — covered by `*.db` / `data/*.db` in
  `.gitignore`; back it up (see `docs/DEPLOYMENT.md`).
- `scripts/seed.py` re-runs seeding manually; set `PULSEPIPE_SEED_ON_START=false`
  in production after the first boot if you want boot to stay read-only.
