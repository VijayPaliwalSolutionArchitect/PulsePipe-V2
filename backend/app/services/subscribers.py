"""Subscriber registration on pipelines."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.database import Database, get_db
from app.schemas import SubscriberCreate

PIPELINE_ERR = "FOREIGN KEY constraint failed"


def _utcnow() -> str:
    """Return a UTC ISO-8601 timestamp string."""
    return datetime.now(timezone.utc).isoformat()


def _hydrate(db: Database, row: dict) -> dict:
    """Load the pipeline name alongside a subscriber row (if applicable)."""
    # row may already be joined or bare; be defensive.
    return row


def list_subscribers(pipeline_id: int, db: Optional[Database] = None) -> list[dict]:
    """Return all subscribers registered on a pipeline."""
    db = db or get_db()
    return db.query(
        "SELECT * FROM subscribers WHERE pipeline_id = ? ORDER BY id", (pipeline_id,)
    )


def create_subscriber(
    pipeline_id: int, data: SubscriberCreate, db: Optional[Database] = None
) -> dict:
    """Register a subscriber; raises ``ValueError`` when the pipeline is absent."""
    db = db or get_db()
    try:
        sid = db.execute(
            """
            INSERT INTO subscribers (pipeline_id, name, endpoint, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (pipeline_id, data.name, data.endpoint, _utcnow()),
        )
    except Exception as exc:  # surfaced as 404 by the router
        if PIPELINE_ERR in str(exc):
            raise LookupError(f"pipeline {pipeline_id} does not exist") from exc
        raise
    row = db.query_one("SELECT * FROM subscribers WHERE id = ?", (sid,))
    assert row is not None
    return row


def delete_subscriber(subscriber_id: int, db: Optional[Database] = None) -> bool:
    """Remove a subscriber; returns False if it did not exist."""
    db = db or get_db()
    cur = db.connect().execute("DELETE FROM subscribers WHERE id = ?", (subscriber_id,))
    db.connect().commit()
    return cur.rowcount > 0


def all_subscribers(db: Optional[Database] = None) -> list[dict]:
    """Return every subscriber across all pipelines."""
    db = db or get_db()
    return db.query(
        """
        SELECT s.*, p.name AS pipeline
        FROM subscribers s
        JOIN pipelines p ON p.id = s.pipeline_id
        ORDER BY s.id
        """
    )