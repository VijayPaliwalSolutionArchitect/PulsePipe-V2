from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.common.db import db
from services.orchestrator.sequence_manager import sequence_orchestrator

router = APIRouter()


class SequenceDispatchRequest(BaseModel):
    step_number: int = 1
    tenant_id: str = "acme-sales"


@router.get("/{campaign_id}")
def get_sequences(campaign_id: str):
    return db.get_sequences(campaign_id)


@router.post("/{campaign_id}/dispatch")
def dispatch_sequence(campaign_id: str, req: SequenceDispatchRequest):
    res = sequence_orchestrator.dispatch_campaign_step(
        tenant_id=req.tenant_id,
        campaign_id=campaign_id,
        step_number=req.step_number
    )
    return res
