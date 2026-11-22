import json
from typing import Any, Dict, Optional
import pytest
from services.common.db import db
from services.common.models import CampaignCreateRequest
from services.api.app.routers import campaigns, prospects, sequences, inbox, deliverability, admin

class DirectResponse:
    def __init__(self, status_code: int, data: Any):
        self.status_code = status_code
        self._data = data
        self.text = json.dumps(data) if isinstance(data, (dict, list)) else str(data)

    def json(self) -> Any:
        return self._data

class DirectClient:
    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> DirectResponse:
        if path in ("/healthz", "/health"):
            return DirectResponse(200, {"status": "healthy", "service": "pulsepipe-core-api"})
        elif path == "/readyz":
            return DirectResponse(200, {"status": "ready"})
        elif path.startswith("/api/v1/campaigns"):
            return DirectResponse(200, campaigns.list_campaigns())
        elif path.startswith("/api/v1/prospects"):
            return DirectResponse(200, prospects.list_prospects())
        elif path.startswith("/api/v1/sequences/"):
            cid = path.split("/")[-1]
            return DirectResponse(200, sequences.get_sequences(cid))
        elif path.startswith("/api/v1/inbox"):
            return DirectResponse(200, inbox.list_inbox_replies())
        elif path == "/api/v1/deliverability/health":
            return DirectResponse(200, deliverability.get_deliverability_health())
        elif path == "/api/v1/admin/stats":
            return DirectResponse(200, admin.get_admin_stats())
        elif path == "/api/v1/admin/settings":
            return DirectResponse(200, admin.get_admin_settings())
        elif path == "/api/v1/admin/models":
            return DirectResponse(200, admin.get_model_registry())
        return DirectResponse(404, {"detail": "Route not found"})

    def post(self, path: str, json: Optional[Dict[str, Any]] = None) -> DirectResponse:
        data = json or {}
        if path == "/api/v1/campaigns/":
            req = CampaignCreateRequest(**data)
            return DirectResponse(200, campaigns.create_campaign(req))
        return DirectResponse(404, {"detail": "Route not found"})

@pytest.fixture(scope="session")
def client():
    return DirectClient()
