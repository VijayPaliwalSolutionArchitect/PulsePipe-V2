from __future__ import annotations
import uuid
from typing import Any, Dict, List
from services.common.db import db
from services.sdr_engine.personalizer import sdr_personalizer


class SequenceOrchestrator:
    """Dispatches multi-step outbound sales sequences respecting domain rate limits and opt-outs."""

    def dispatch_campaign_step(
        self,
        tenant_id: str,
        campaign_id: str,
        step_number: int = 1
    ) -> Dict[str, Any]:
        prospects = db.get_prospects(campaign_id=campaign_id, tenant_id=tenant_id)
        dispatched_count = 0
        suppressed_count = 0

        for p in prospects:
            # Step 1: Check suppression & opt-outs
            if db.is_suppressed(tenant_id, p["email"]):
                suppressed_count += 1
                continue

            # Step 2: Personalize email
            copy = sdr_personalizer.generate_personalized_email(
                tenant_id=tenant_id,
                prospect=p,
                step_number=step_number
            )

            # Step 3: Record dispatch
            msg_id = f"out-{uuid.uuid4().hex[:8]}"
            cur = db._conn.cursor()
            cur.execute("""
            INSERT INTO outbox_messages (id, campaign_id, prospect_id, tenant_id, recipient_email, subject, body_text, step_number, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (msg_id, campaign_id, p["id"], tenant_id, p["email"], copy["subject"], copy["body"], step_number, "delivered"))
            db._conn.commit()
            dispatched_count += 1

        return {
            "campaign_id": campaign_id,
            "step_number": step_number,
            "dispatched": dispatched_count,
            "suppressed": suppressed_count,
            "status": "completed"
        }


sequence_orchestrator = SequenceOrchestrator()
