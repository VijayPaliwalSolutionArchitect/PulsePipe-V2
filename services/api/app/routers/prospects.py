from typing import Optional
from fastapi import APIRouter
from services.common.db import db

router = APIRouter()


@router.get("/")
def list_prospects(campaign_id: Optional[str] = None, tenant_id: str = "acme-sales"):
    return db.get_prospects(campaign_id=campaign_id, tenant_id=tenant_id)
