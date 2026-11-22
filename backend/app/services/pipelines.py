"""CRUD operations for named pipelines."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.database import Database, get_db
from app.schemas import PipelineCreate, PipelineUpdate

UNIQUE_ERR = "UNIQUE constraint failed"


def _utcnow() -> str:
    """Return a UTC ISO-8601 timestamp string."""
    return datetime.now(timezone.utc).isoformat()


def list_pipelines(db: Optional[Database] = None) -> list[dict]:
    """Return all pipelines with aggregated event/subscriber counts."""
    db = db or get_db()
    rows = db.query(
        """
        SELECT p.*, COUNT(DISTINCT e.id) AS event_count,
               (SELECT COUNT(*) FROM subscribers s WHERE s.pipeline_id = p.id)
                   AS subscriber_count
        FROM pipelines p
        LEFT JOIN events e ON e.pipeline_id = p.id
        GROUP BY p.id
        ORDER BY p.id
        """
    )
    for row in rows:
        row["transform_spec"] = db.loads(row["transform_spec"], [])
        row["sinks"] = db.loads(row["sinks"], [])
    return rows


def get_pipeline(pipeline_id: int, db: Optional[Database] = None) -> Optional[dict]:
    """Return a single pipeline (with counts) or ``None``."""
    db = db or get_db()
    row = db.query_one(
        """
        SELECT p.*, COUNT(DISTINCT e.id) AS event_count,
               (SELECT COUNT(*) FROM subscribers s WHERE s.pipeline_id = p.id)
                   AS subscriber_count
        FROM pipelines p
        LEFT JOIN events e ON e.pipeline_id = p.id
        WHERE p.id = ?
        GROUP BY p.id
        """,
        (pipeline_id,),
    )
    if row:
        row["transform_spec"] = db.loads(row["transform_spec"], [])
        row["sinks"] = db.loads(row["sinks"], [])
    return row


def create_pipeline(data: PipelineCreate, db: Optional[Database] = None) -> dict:
    """Create a pipeline and return its stored record."""
    db = db or get_db()
    now = _utcnow()
    try:
        pid = db.execute(
            """
            INSERT INTO pipelines
                (name, description, source, transform_spec, sinks, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.name,
                data.description,
                data.source,
                db.dumps(data.transform_spec),
                db.dumps(data.sinks),
                now,
                now,
            ),
        )
    except Exception as exc:  # surfaced as 409 by the router
        if UNIQUE_ERR in str(exc):
            raise ValueError(f"pipeline '{data.name}' already exists") from exc
        raise
    created = get_pipeline(pid, db)
    assert created is not None
    return created


def update_pipeline(
    pipeline_id: int, data: PipelineUpdate, db: Optional[Database] = None
) -> Optional[dict]:
    """Patch an existing pipeline's fields, returning the updated record."""
    db = db or get_db()
    existing = db.query_one("SELECT * FROM pipelines WHERE id = ?", (pipeline_id,))
    if existing is None:
        return None

    new_desc = data.description if data.description is not None else existing["description"]
    new_source = data.source if data.source is not None else existing["source"]
    new_spec = (
        data.transform_spec
        if data.transform_spec is not None
        else db.loads(existing["transform_spec"], [])
    )
    new_sinks = (
        data.sinks if data.sinks is not None else db.loads(existing["sinks"], [])
    )
    db.execute(
        """
        UPDATE pipelines
        SET description = ?, source = ?, transform_spec = ?, sinks = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            new_desc,
            new_source,
            db.dumps(new_spec),
            db.dumps(new_sinks),
            _utcnow(),
            pipeline_id,
        ),
    )
    return get_pipeline(pipeline_id, db)


def delete_pipeline(pipeline_id: int, db: Optional[Database] = None) -> bool:
    """Delete a pipeline. Cascades to events, subscribers and alerts."""
    db = db or get_db()
    cur = db.connect().execute("DELETE FROM pipelines WHERE id = ?", (pipeline_id,))
    affected = cur.rowcount
    db.connect().commit()
    return affected > 0


def find_by_name(name: str, db: Optional[Database] = None) -> Optional[dict]:
    """Look up a pipeline by its unique name."""
    db = db or get_db()
    row = db.query_one("SELECT * FROM pipelines WHERE name = ?", (name,))
    if row:
        row["transform_spec"] = db.loads(row["transform_spec"], [])
        row["sinks"] = db.loads(row["sinks"], [])
    return row


def as_dict(row: dict) -> dict[str, Any]:
    """Normalize a DB row into a serializable pipeline dict."""
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "source": row["source"],
        "transform_spec": row["transform_spec"],
        "sinks": row["sinks"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }