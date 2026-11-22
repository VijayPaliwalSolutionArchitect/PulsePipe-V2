from fastapi import APIRouter
from services.common.db import db

router = APIRouter()


@router.get("/health")
def get_deliverability_health(tenant_id: str = "acme-sales"):
    t = db.get_tenant(tenant_id)
    domain = t.get("sending_domain", "outbound.acme.com") if t else "outbound.acme.com"

    return {
        "sending_domain": domain,
        "reputation_score": 98.4,
        "reputation_status": "HIGH",
        "dns_records": {
            "spf": {"status": "PASS", "record": "v=spf1 include:_spf.google.com ~all"},
            "dkim": {"status": "PASS", "selector": "pulsepipe._domainkey", "key_size": 2048},
            "dmarc": {"status": "PASS", "policy": "reject", "pct": 100}
        },
        "bounce_metrics": {
            "hard_bounce_rate": "0.12%",
            "soft_bounce_rate": "0.45%",
            "threshold_limit": "2.00%"
        },
        "daily_throttle": {
            "sent_today": 85,
            "max_daily_limit": 500,
            "cooldown_seconds": 12
        }
    }
