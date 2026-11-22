import uuid
from fastapi import APIRouter
from services.common.db import db
from services.common.models import CampaignCreateRequest

router = APIRouter()


@router.get("/")
def list_campaigns(tenant_id: str = "acme-sales"):
    return db.get_campaigns(tenant_id)


@router.post("/")
def create_campaign(req: CampaignCreateRequest):
    cid = f"camp-{uuid.uuid4().hex[:8]}"
    db.add_campaign({
        "id": cid,
        "tenant_id": req.tenant_id or "acme-sales",
        "title": req.title,
        "target_segment": req.target_segment,
        "sdr_persona": req.sdr_persona,
        "model_pool": req.model_pool,
        "daily_send_limit": req.daily_send_limit
    })
    return {"status": "created", "id": cid, "title": req.title}
