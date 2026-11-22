"""SQLite storage layer for PulsePipe.

Uses the standard-library ``sqlite3`` module directly. A single shared
connection is created per process and guarded by a lock so concurrent request
handlers can share it safely. SQLite is intentionally the persistence layer of
choice here: zero external services, file-based, trivial to back up.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Optional, Sequence

SCHEMA = """
CREATE TABLE IF NOT EXISTS pipelines (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL UNIQUE,
    description   TEXT NOT NULL DEFAULT '',
    source        TEXT NOT NULL DEFAULT '',
    transform_spec TEXT NOT NULL DEFAULT '[]',
    sinks         TEXT NOT NULL DEFAULT '[]',
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subscribers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_id INTEGER NOT NULL,
    name        TEXT NOT NULL,
    endpoint    TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    FOREIGN KEY (pipeline_id) REFERENCES pipelines (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id     TEXT NOT NULL,
    pipeline_id  INTEGER NOT NULL,
    payload      TEXT NOT NULL,          -- JSON object
    received_at  TEXT NOT NULL,          -- ISO-8601 UTC
    emitted_at   TEXT,                   -- NULL until dispatched to a subscriber
    status       TEXT NOT NULL DEFAULT 'received',
    dedup        INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (pipeline_id) REFERENCES pipelines (id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_events_pipeline ON events (pipeline_id);
CREATE INDEX IF NOT EXISTS idx_events_eventid  ON events (event_id, pipeline_id);

CREATE TABLE IF NOT EXISTS alert_rules (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_id INTEGER NOT NULL,
    name        TEXT NOT NULL,
    rule_type   TEXT NOT NULL CHECK (rule_type IN ('keyword','threshold')),
    config      TEXT NOT NULL DEFAULT '{}',
    enabled     INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL,
    FOREIGN KEY (pipeline_id) REFERENCES pipelines (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alerts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id     INTEGER NOT NULL,
    pipeline_id INTEGER NOT NULL,
    severity    TEXT NOT NULL DEFAULT 'warning',
    message     TEXT NOT NULL,
    event_ids   TEXT NOT NULL DEFAULT '[]',   -- JSON array of matching events
    triggered_at TEXT NOT NULL,
    FOREIGN KEY (rule_id) REFERENCES alert_rules (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS replay_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_id  INTEGER NOT NULL,
    event_id     TEXT NOT NULL,
    source       TEXT NOT NULL,             -- 'manual' | 'event' | 'window'
    replayed_at  TEXT NOT NULL
);
"""


class Database:
    """Thread-safe wrapper around a SQLite connection."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Return the shared connection, initialising it on first use."""
        with self._lock:
            if self._conn is None:
                self._conn = sqlite3.connect(
                    str(self.path), check_same_thread=False
                )
                self._conn.row_factory = sqlite3.Row
                self._conn.execute("PRAGMA foreign_keys = ON")
                self._conn.executescript(SCHEMA)
                self._conn.commit()
            return self._conn

    def close(self) -> None:
        """Close the underlying connection if open."""
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    # ---- helpers -------------------------------------------------------
    def execute(self, sql: str, params: Sequence[Any] = ()) -> int:
        """Run a write statement and return the last inserted row id."""
        conn = self.connect()
        with self._lock:
            cur = conn.execute(sql, params)
            conn.commit()
            return cur.lastrowid or 0

    def executemany(self, sql: str, seq: Sequence[Sequence[Any]]) -> None:
        """Run a write statement for many parameter sets and commit."""
        conn = self.connect()
        with self._lock:
            conn.executemany(sql, seq)
            conn.commit()

    def query(self, sql: str, params: Sequence[Any] = ()) -> list[dict]:
        """Run a read statement and return rows as plain dictionaries."""
        conn = self.connect()
        with self._lock:
            cur = conn.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]

    def query_one(
        self, sql: str, params: Sequence[Any] = ()
    ) -> Optional[dict]:
        """Run a read statement and return the first row, or ``None``."""
        rows = self.query(sql, params)
        return rows[0] if rows else None

    # ---- JSON helpers -------------------------------------------------
    @staticmethod
    def dumps(value: Any) -> str:
        """Serialize a Python object to a JSON string for a TEXT column."""
        return json.dumps(value, separators=(",", ":"))

    @staticmethod
    def loads(value: Optional[str], default: Any = None) -> Any:
        """Deserialize a JSON TEXT column (``default`` on missing data)."""
        if value is None:
            return default
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return default if default is not None else value


_db: Optional[Database] = None


def get_db() -> Database:
    """Return the process-global :class:`Database` instance.

    Lazily constructed on first use so importing modules does not open a
    connection before app startup configures the path.
    """
    global _db
    if _db is None:
        from app.config import settings  # local import avoids circularity

        _db = Database(settings.database_path)
    return _db