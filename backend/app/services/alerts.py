"""Alert rule evaluation.

Two rule types are supported, both scoped to a pipeline:

* ``keyword``   — fire when any recent event payload for the pipeline contains
  the configured substring.  Used to catch high-value or error-laden events,
  e.g. any payload containing ``"error"`` or ``"chargeback"``.
* ``threshold`` — fire when at least ``threshold`` events arrive for the
  pipeline within ``window_seconds``.  Used for rate/volume spikes.

Rules can be created with no ``pipeline_id`` to apply across all pipelines.
Evaluation is pull-based: callers invoke ``evaluate_rules`` (the
``POST /api/alerts/evaluate`` endpoint) and every fired alert is persisted to
the ``alerts`` table.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.database import Database, get_db


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse(ts: str) -> datetime:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.now(timezone.utc)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def _load_config(db: Database, raw: str) -> dict[str, Any]:
    config = db.loads(raw, {})
    return config if isinstance(config, dict) else {}


def _fire(
    db: Database,
    rule: dict,
    message: str,
    event_ids: list[str],
    severity: str,
) -> None:
    db.execute(
        "INSERT INTO alerts (rule_id, pipeline_id, severity, message, event_ids, triggered_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            rule["id"],
            rule["pipeline_id"],
            severity,
            message,
            db.dumps(event_ids),
            _utcnow(),
        ),
    )


def _evaluate_keyword(
    db: Database, rule: dict, config: dict, events: list[dict]
) -> Optional[dict]:
    keyword = config.get("keyword", "")
    if not keyword:
        return None
    matched = [
        row for row in events
        if keyword.lower() in (row["payload_text"] or "").lower()
    ]
    if not matched:
        return None
    ids = [m["event_id"] for m in matched]
    message = f"keyword '{keyword}' seen in {len(ids)} event(s)"
    return {
        "event_ids": ids,
        "message": message,
        "severity": config.get("severity", rule.get("severity", "warning")),
    }


def _evaluate_threshold(
    db: Database, rule: dict, config: dict, events: list[dict]
) -> Optional[dict]:
    threshold = int(config.get("threshold", 0) or 0)
    window = int(config.get("window_seconds", 60) or 60)
    if threshold <= 0:
        return None
    start = datetime.now(timezone.utc) - timedelta(seconds=window)
    recent = [row for row in events if _parse(row["received_at"]) >= start]
    if len(recent) < threshold:
        return None
    ids = [m["event_id"] for m in recent]
    message = (
        f"threshold hit: {len(recent)} event(s) in {window}s "
        f"(>= {threshold})"
    )
    return {
        "event_ids": ids,
        "message": message,
        "severity": config.get("severity", rule.get("severity", "warning")),
    }


def evaluate_rules(db: Optional[Database] = None) -> dict:
    """Evaluate every enabled alert rule and persist any that fire.

    Returns ``{"rules_evaluated", "alerts_fired", "alerts"}``.
    """
    db = db or get_db()
    rules = db.query(
        "SELECT ar.*, p.name AS pipeline FROM alert_rules ar "
        "LEFT JOIN pipelines p ON p.id = ar.pipeline_id WHERE ar.enabled = 1"
    )
    fired: list[dict] = []

    for rule in rules:
        config = _load_config(db, rule["config"])
        if rule["pipeline_id"]:
            events = db.query(
                "SELECT event_id, payload, received_at FROM events WHERE pipeline_id = ?",
                (rule["pipeline_id"],),
            )
        else:
            events = db.query("SELECT event_id, payload, received_at FROM events")
        for row in events:
            row["payload_text"] = (
                row["payload"] if isinstance(row["payload"], str) else json.dumps(row["payload"])
            )

        result = None
        if rule["rule_type"] == "keyword":
            result = _evaluate_keyword(db, rule, config, events)
        elif rule["rule_type"] == "threshold":
            result = _evaluate_threshold(db, rule, config, events)

        if result:
            _fire(
                db,
                rule,
                result["message"],
                result["event_ids"],
                result["severity"],
            )
            fired.append(_serialize(db, rule, result))

    return {"rules_evaluated": len(rules), "alerts_fired": len(fired), "alerts": fired}


def _serialize(db: Database, rule: dict, result: dict) -> dict:
    now = _utcnow()
    return {
        "id": 0,
        "rule_id": rule["id"],
        "pipeline_id": rule["pipeline_id"],
        "pipeline": rule.get("pipeline", ""),
        "severity": result["severity"],
        "message": result["message"],
        "event_ids": result["event_ids"],
        "triggered_at": now,
    }


def list_rules(db: Optional[Database] = None) -> list[dict]:
    """Return alert rules, newest first."""
    db = db or get_db()
    rows = db.query(
        "SELECT ar.*, p.name AS pipeline FROM alert_rules ar "
        "LEFT JOIN pipelines p ON p.id = ar.pipeline_id ORDER BY ar.id DESC"
    )
    for row in rows:
        row["config"] = _load_config(db, row["config"])
        row["enabled"] = bool(row["enabled"])
    return rows


def list_alerts(limit: int = 50, db: Optional[Database] = None) -> list[dict]:
    """Return fired alerts, newest first."""
    db = db or get_db()
    rows = db.query(
        "SELECT a.*, p.name AS pipeline FROM alerts a "
        "JOIN pipelines p ON p.id = a.pipeline_id ORDER BY a.id DESC LIMIT ?",
        (limit,),
    )
    for row in rows:
        row["event_ids"] = db.loads(row["event_ids"], [])
    return rows


def create_rule(
    name: str,
    rule_type: str,
    pipeline_id: Optional[int],
    config: dict,
    enabled: bool = True,
    db: Optional[Database] = None,
) -> dict:
    """Persist a new alert rule, returning its stored record."""
    db = db or get_db()
    exists = (
        db.query_one("SELECT id FROM pipelines WHERE id = ?", (pipeline_id,))
        if pipeline_id is not None
        else {"id": 1}  # global rules are always valid
    )
    if exists is None:
        raise LookupError(f"pipeline {pipeline_id} does not exist")
    rule_id = db.execute(
        "INSERT INTO alert_rules (pipeline_id, name, rule_type, config, enabled, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            pipeline_id if pipeline_id is not None else None,
            name,
            rule_type,
            db.dumps(config),
            1 if enabled else 0,
            _utcnow(),
        ),
    )
    row = db.query_one("SELECT * FROM alert_rules WHERE id = ?", (rule_id,))
    assert row is not None
    row["config"] = _load_config(db, row["config"])
    row["enabled"] = bool(row["enabled"])
    return row