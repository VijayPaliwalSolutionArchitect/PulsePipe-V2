from services.orchestrator.sequence_manager import sequence_orchestrator
from services.common.db import db

def test_sequence_dispatch_respects_suppressions():
    # Make sure kevin@unsub.example is suppressed
    assert db.is_suppressed("acme-sales", "kevin@unsub.example") is True

    res = sequence_orchestrator.dispatch_campaign_step(
        tenant_id="acme-sales",
        campaign_id="camp-01",
        step_number=1
    )
    assert res["status"] == "completed"
    assert res["dispatched"] >= 1
    assert res["suppressed"] >= 1
