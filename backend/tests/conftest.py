"""Shared fixtures for the PulsePipe test suite.

The database is redirected to a throwaway temp file and seeding is disabled
so every test starts against an empty, predictable store.  A tiny in-process
HTTP server stands in for a real subscriber so dispatch can be exercised
end-to-end without any external network.
"""

from __future__ import annotations

import os
import socketserver
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler

import pytest

# --- Point the app at a throwaway DB before importing it. ----------------
_TMP = tempfile.mkdtemp(prefix="pulsepipe-test-")
os.environ["PULSEPIPE_DB_PATH"] = os.path.join(_TMP, "test.db")
os.environ["PULSEPIPE_SEED_ON_START"] = "false"
os.environ["PULSEPIPE_DISPATCH_MODE"] = "sync"
os.environ["PULSEPIPE_DISPATCH_TIMEOUT"] = "2.0"

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from fastapi.testclient import TestClient  # noqa: E402

from main import create_app  # noqa: E402


class _EchoHandler(BaseHTTPRequestHandler):
    """Accepts any request and returns 200 with a JSON ack."""

    def do_POST(self):  # noqa: N802
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ack": true, "n": ' + str(len(body)).encode() + b'}')

    def log_message(self, *args):  # silence request logging
        pass


@pytest.fixture(scope="session")
def echo_server():
    """A local HTTP 200 endpoint usable as a subscriber."""
    with socketserver.TCPServer(("127.0.0.1", 0), _EchoHandler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        yield f"http://{host}:{port}/hook"
        server.shutdown()
        thread.join(timeout=2)


@pytest.fixture()
def client():
    """A TestClient with a freshly configured app (empty DB, no seed)."""
    with TestClient(create_app()) as c:
        yield c


@pytest.fixture(autouse=True)
def _clean_events():
    """Wipe the events/alert tables between tests for a clean slate."""
    from app.database import get_db

    db = get_db()
    for table in ("alerts", "events", "replay_log", "subscribers"):
        db.execute(f"DELETE FROM {table}")
    db.execute("DELETE FROM alert_rules")
    # pipelines are shared/reused across tests by design
    yield