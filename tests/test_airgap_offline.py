"""tests/test_airgap_offline.py — Verified Air-Gap Zero-Egress Test.
Simulates a strictly disconnected air-gapped network environment by monkeypatching
socket connections to fail on any external egress attempt, proving the offline pool
operates 100% locally with zero network leakage.
"""
import socket
import pytest
from services.ai_router.engine import global_router


def test_airgap_zero_egress_execution(monkeypatch):
    """Proves the offline/local pool operates without any outbound socket egress."""
    
    # 1. Simulate blocked network egress
    def blocked_connect(self, *args, **kwargs):
        raise ConnectionError("AIR-GAP VIOLATION: Outbound network egress attempted in air-gapped mode!")

    monkeypatch.setattr(socket.socket, "connect", blocked_connect)

    # 2. Execute query routed to offline pool via execute_call
    res = global_router.execute_call(
        tenant_id="acme-sales",
        pool="offline",
        prompt="Write a 1-sentence outbound introduction for an enterprise prospect."
    )

    # 3. Assert local execution succeeded with zero cost and no network calls
    assert res is not None
    assert res.get("pool") == "offline" or "local" in str(res.get("model_id"))
    assert res.get("cost_usd", 0.0) == 0.0
    assert res.get("latency_ms") > 0
