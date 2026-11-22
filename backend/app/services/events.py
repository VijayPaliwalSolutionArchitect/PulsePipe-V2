"""Event ingestion, dedup, transform application and subscriber dispatch.

An event enters the system via ``POST /api/events``.  It is:

1. Deduplicated on ``(event_id, pipeline_id)`` — a repeat send of the same
   key returns the stored event and does **not** dispatch again.
2. Run through the pipeline's ordered transform list (see ``transforms.py``).
3. Stored in the ``events`` table with a ``received`` status.
4. Dispatched to every subscriber registered on the pipeline, either inline
   (sync mode — deterministic, easier to reason about) or on a daemon thread
   (async mode — non-blocking ingest).

Every delivery attempt produces an :class:`EmitResult` so callers can see
exactly what went to which endpoint and whether it was accepted.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.config import settings
from app.database import Database, get_db
from app.schemas import EmitResult, EventIngest
from app.services import subscribers as subscriber_svc
from app.services.pipelines import find_by_name
from app.services.transforms import apply_transforms

log = logging.getLogger(__name__)


def _utcnow() -> str:
    """Return a UTC ISO-8601 timestamp string."""
    return datetime.now(timezone.utc).isoformat()


def _deliver(
    endpoint: str, payload: dict, event_id: str, timeout: float
) -> tuple[bool, str]:
    """POST one event to a subscriber endpoint.

    Returns ``(ok, detail)``.  Anything below HTTP 400 counts as accepted;
    the body we POST wraps the original payload plus identifying metadata so
    a subscriber can correlate the delivery back to the stored event.
    """
    body = {"event_id": event_id, "payload": payload, "emitted_at": _utcnow()}
    try:
        resp = httpx.post(endpoint, json=body, timeout=timeout)
        ok = resp.status_code < 400
        return ok, f"HTTP {resp.status_code}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _mark_emitted(db: Database, pipeline_id: int, event_id: str, ok: bool) -> None:
    """Flip an event's status/emitted_at after a dispatch attempt."""
    status = "emitted" if ok else "failed"
    db.execute(
        "UPDATE events SET status = ?, emitted_at = ? WHERE event_id = ? AND pipeline_id = ?",
        (status, _utcnow(), event_id, pipeline_id),
    )


def dispatch_event(
    pipeline_id: int, event_id: str, payload: dict
) -> list[EmitResult]:
    """Deliver one stored event to every subscriber of its pipeline (sync)."""
    db = get_db()
    results: list[EmitResult] = []
    for sub in subscriber_svc.list_subscribers(pipeline_id, db):
        ok, detail = _deliver(sub["endpoint"], payload, event_id, settings.dispatch_timeout)
        results.append(
            EmitResult(
                subscriber_id=sub["id"],
                subscriber_name=sub["name"],
                endpoint=sub["endpoint"],
                ok=ok,
                detail=detail,
            )
        )
    _mark_emitted(db, pipeline_id, event_id, any(r.ok for r in results))
    return results


def _dispatch_async(pipeline_id: int, event_id: str, payload: dict) -> None:
    """Dispatch on a daemon thread so ingest returns immediately."""

    def _run() -> None:
        try:
            dispatch_event(pipeline_id, event_id, payload)
        except Exception:  # never let a background failure kill the app
            log.exception("async dispatch failed for event %s", event_id)

    threading.Thread(target=_run, daemon=True).start()


def ingest(
    data: EventIngest, db: Optional[Database] = None
) -> tuple[dict, list[EmitResult], bool]:
    """Run the full ingest pipeline for one event.

    Returns ``(stored_event_dict, deliver_results, is_dedup)``.

    Raises :class:`LookupError` when the named pipeline does not exist, so the
    caller (router) can translate that into an HTTP 404.
    """
    db = db or get_db()
    pipeline = find_by_name(data.pipeline, db)
    if pipeline is None:
        raise LookupError(f"pipeline '{data.pipeline}' does not exist")

    pipeline_id = pipeline["id"]

    # 1. Dedup — a re-sent key is returned as-is, never re-transformed or
    #    re-dispatched.
    existing = db.query_one(
        "SELECT * FROM events WHERE event_id = ? AND pipeline_id = ?",
        (data.event_id, pipeline_id),
    )
    if existing is not None:
        existing["payload"] = db.loads(existing["payload"], {})
        # Flag the earlier stored row as a dedup hit too.
        db.execute(
            "UPDATE events SET dedup = 1 WHERE id = ?", (existing["id"],)
        )
        existing["dedup"] = True
        return existing, [], True

    # 2. Transform — payload is deep-copied; the pipeline's rules are applied
    #    in order.  The original payload dict is never mutated.
    payload, _applied = apply_transforms(data.payload, pipeline["transform_spec"])

    # 3. Store.
    row_id = db.execute(
        "INSERT INTO events (event_id, pipeline_id, payload, received_at, status, dedup) "
        "VALUES (?, ?, ?, ?, 'received', 0)",
        (data.event_id, pipeline_id, db.dumps(payload), _utcnow()),
    )
    stored = db.query_one("SELECT * FROM events WHERE id = ?", (row_id,))
    assert stored is not None
    stored["payload"] = payload

    # 4. Dispatch.
    if settings.is_async_dispatch:
        _dispatch_async(pipeline_id, data.event_id, payload)
        return stored, [], False

    results = dispatch_event(pipeline_id, data.event_id, payload)
    # Reflect the delivery outcome on the returned row (the DB was already
    # updated inside dispatch_event).
    if any(r.ok for r in results):
        stored["status"] = "emitted"
    elif results:
        stored["status"] = "failed"
    stored["emitted_at"] = _utcnow() if results else stored.get("emitted_at")
    return stored, results, False


def list_events(
    pipeline_id: Optional[int] = None, limit: int = 50, db: Optional[Database] = None
) -> list[dict]:
    """Return stored events, newest first, optionally filtered by pipeline."""
    db = db or get_db()
    sql = (
        "SELECT e.*, p.name AS pipeline FROM events e "
        "JOIN pipelines p ON p.id = e.pipeline_id"
    )
    params: tuple = ()
    if pipeline_id is not None:
        sql += " WHERE e.pipeline_id = ?"
        params = (pipeline_id,)
    sql += " ORDER BY e.id DESC LIMIT ?"
    rows = db.query(sql, params + (limit,))
    for row in rows:
        row["payload"] = db.loads(row["payload"], {})
    return rows


def get_event(event_id: int, db: Optional[Database] = None) -> Optional[dict]:
    """Return a single stored event row, or ``None``."""
    db = db or get_db()
    row = db.query_one(
        "SELECT e.*, p.name AS pipeline FROM events e "
        "JOIN pipelines p ON p.id = e.pipeline_id WHERE e.id = ?",
        (event_id,),
    )
    if row:
        row["payload"] = db.loads(row["payload"], {})
    return row