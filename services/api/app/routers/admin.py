from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
from services.common.db import db
from services.ai_router.engine import global_router, DEFAULT_POOLS
from services.common.config import settings

router = APIRouter()


class PersonaUpdateRequest(BaseModel):
    persona_id: str
    tone: str
    system_prompt: str


class AddSuppressionRequest(BaseModel):
    email: str
    reason: str = "manual_opt_out"
    tenant_id: str = "acme-sales"


@router.get("/stats")
def get_admin_stats(tenant_id: str = "acme-sales"):
    campaigns = db.get_campaigns(tenant_id)
    prospects = db.get_prospects(tenant_id=tenant_id)
    replies = db.get_replies(tenant_id)
    suppressions = db.get_suppressions(tenant_id)
    t = db.get_tenant(tenant_id) or {"current_spend_usd": 0.0, "monthly_budget_usd": 200.0, "hard_cap_usd": 250.0}

    interested_count = sum(1 for r in replies if r["reply_intent"] == "interested")

    return {
        "active_campaigns": len(campaigns),
        "total_prospects": len(prospects),
        "total_replies": len(replies),
        "interested_leads": interested_count,
        "suppressed_emails": len(suppressions),
        "current_spend_usd": t["current_spend_usd"],
        "monthly_budget_usd": t["monthly_budget_usd"],
        "hard_cap_usd": t["hard_cap_usd"],
        "system_health": "100% operational"
    }


@router.get("/settings")
def get_admin_settings():
    return {
        "app": {
            "name": "PulsePipe AI SDR Outbound Engine",
            "version": "2.0.0",
            "env": settings.ENV,
            "simulate": settings.SIMULATE,
            "max_emails_per_hour_domain": settings.MAX_EMAILS_PER_HOUR_DOMAIN
        },
        "compliance": {
            "can_spam": "Compliant (Footer Physical Address & Unsubscribe Enforcement)",
            "gdpr": "Right to Erasure & Auto-Suppression Active",
            "dpdp_2023": "PII Masking Active"
        }
    }


@router.get("/models")
def get_model_registry():
    return {
        "models": {k: v.__dict__ for k, v in global_router.registry.items()},
        "pools": {k: v for k, v in DEFAULT_POOLS.items()},
        "ledger": global_router.ledger.get_summary()
    }


@router.get("/personas")
def get_personas(tenant_id: str = "acme-sales"):
    return db.get_personas(tenant_id)


@router.post("/personas/update")
def update_persona(req: PersonaUpdateRequest):
    db.update_persona(req.persona_id, req.system_prompt, req.tone)
    return {"status": "updated", "id": req.persona_id}


@router.get("/suppressions")
def get_suppressions(tenant_id: str = "acme-sales"):
    return db.get_suppressions(tenant_id)


@router.post("/suppressions")
def add_suppression(req: AddSuppressionRequest):
    db.add_suppression(req.tenant_id, req.email, req.reason)
    return {"status": "suppressed", "email": req.email}


@router.get("/traces")
def get_traces(tenant_id: str = "acme-sales"):
    return db.get_audit_logs(tenant_id)
