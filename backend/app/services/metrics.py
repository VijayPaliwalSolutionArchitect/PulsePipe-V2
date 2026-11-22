"""Throughput, counts, latency and queue metrics for stored events.

All metrics are computed live from the ``events`` table on every call so the
numbers always reflect the current state (no background aggregator to keep in
sync).  Timestamps are ISO-8601 strings with a UTC offset; we parse them with
``datetime.fromisoformat`` and compare in naive-UTC space.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from app.database import Database, get_db


def _parse(ts: str) -> datetime:
    """Parse an ISO-8601 timestamp, falling back to UTC on malformed input."""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _window_start(window_seconds: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(seconds=window_seconds)


def throughput(
    window_seconds: int = 60, db: Optional[Database] = None
) -> dict:
    """Events ingested in the last ``window_seconds`` and their rate."""
    db = db or get_db()
    start = _window_start(window_seconds)
    rows = db.query("SELECT received_at FROM events")
    window_events = [
        r for r in rows if _parse(r["received_at"]) >= start
    ]
    count = len(window_events)
    return {
        "window_seconds": window_seconds,
        "duration_seconds": float(window_seconds),
        "events": count,
        "events_per_second": round(count / window_seconds, 4) if window_seconds else 0.0,
    }


def counts(db: Optional[Database] = None) -> dict:
    """Total events plus a per-pipeline breakdown."""
    db = db or get_db()
    total = db.query_one("SELECT COUNT(*) AS n FROM events")["n"]
    breakdown = db.query(
        "SELECT e.pipeline_id, p.name AS pipeline, COUNT(*) AS events "
        "FROM events e JOIN pipelines p ON p.id = e.pipeline_id "
        "GROUP BY e.pipeline_id ORDER BY e.pipeline_id"
    )
    return {"total_events": total, "pipelines": breakdown}


def latency(db: Optional[Database] = None) -> dict:
    """Receive->emit latency in milliseconds across emitted events."""
    db = db or get_db()
    rows = db.query("SELECT received_at, emitted_at FROM events WHERE emitted_at IS NOT NULL")
    if not rows:
        return {
            "emitted_events": 0,
            "avg_latency_ms": 0.0,
            "max_latency_ms": 0.0,
            "min_latency_ms": 0.0,
            "sample_period": "",
        }
    ms = [
        max(0.0, (_parse(r["emitted_at"]) - _parse(r["received_at"])).total_seconds() * 1000.0)
        for r in rows
    ]
    return {
        "emitted_events": len(ms),
        "avg_latency_ms": round(sum(ms) / len(ms), 2),
        "max_latency_ms": round(max(ms), 2),
        "min_latency_ms": round(min(ms), 2),
        "sample_period": "all-time",
    }


def queue_depth(db: Optional[Database] = None) -> dict:
    """Depth of the in-flight queue: received but not yet emitted."""
    db = db or get_db()
    total = db.query_one(
        "SELECT COUNT(*) AS n FROM events WHERE status = 'received'"
    )["n"]
    by_pipeline = db.query(
        "SELECT e.pipeline_id, p.name AS pipeline, COUNT(*) AS events "
        "FROM events e JOIN pipelines p ON p.id = e.pipeline_id "
        "WHERE e.status = 'received' GROUP BY e.pipeline_id ORDER BY e.pipeline_id"
    )
    return {"total_depth": total, "by_pipeline": by_pipeline}