"""Event replay: re-emit previously stored events to subscribers.

Replaying is useful for backfilling a subscriber that had an outage, or for
re-sending a specific event into a new downstream system.  Exactly one of the
selectors may be used per request:

* ``event_id``             — a single event by its dedup key.
* ``window_from``/``to``   — all events received in an ISO time range.
* ``limit``                — the most recent N events (default when nothing
  else is given).

Every replayed event is appended to the ``replay_log`` table for an audit
trail of what was resent, when, and why.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.database import Database, get_db
from app.schemas import ReplayRequest
from app.services.events import dispatch_event


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _select_events(db: Database, req: ReplayRequest) -> list[dict]:
    """Select events matching exactly one selector."""
    if req.event_id is not None:
        rows = [
            r
            for r in db.query(
                "SELECT * FROM events WHERE event_id = ?", (req.event_id,)
            )
        ]
    elif req.window_from or req.window_to:
        clauses, params = [], []
        if req.window_from:
            clauses.append("received_at >= ?")
            params.append(req.window_from)
        if req.window_to:
            clauses.append("received_at <= ?")
            params.append(req.window_to)
        rows = db.query(
            "SELECT * FROM events WHERE " + " AND ".join(clauses), tuple(params)
        )
    else:
        rows = db.query("SELECT * FROM events ORDER BY id DESC LIMIT ?", (req.limit,))
    for row in rows:
        row["payload"] = db.loads(row["payload"], {})
    return rows


def replay(req: ReplayRequest, db: Optional[Database] = None) -> dict:
    """Re-dispatch selected events to their subscribers.

    Returns ``{"requested", "events_selected", "deliveries", "failures",
    "replayed_at"}``.  Delivery counters reflect per-subscriber attempts, so a
    single event delivered to two subscribers counts as two deliveries.
    """
    db = db or get_db()
    events = _select_events(db, req)

    deliveries = 0
    failures = 0
    for ev in events:
        results = dispatch_event(ev["pipeline_id"], ev["event_id"], ev["payload"])
        for res in results:
            if res.ok:
                deliveries += 1
            else:
                failures += 1
        db.execute(
            "INSERT INTO replay_log (pipeline_id, event_id, source, replayed_at) "
            "VALUES (?, ?, 'manual', ?)",
            (ev["pipeline_id"], ev["event_id"], _utcnow()),
        )

    requested = "limit=%d" % req.limit
    if req.event_id:
        requested = f"event_id={req.event_id}"
    elif req.window_from or req.window_to:
        requested = f"window {req.window_from} -> {req.window_to}"

    return {
        "requested": requested,
        "events_selected": len(events),
        "deliveries": deliveries,
        "failures": failures,
        "replayed_at": _utcnow(),
    }