"""services/api/app/main.py — Core FastAPI Application for PulsePipe V2."""
from __future__ import annotations
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.common.config import settings
from services.api.app.routers import admin, campaigns, prospects, sequences, inbox, deliverability, export

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
_logger = logging.getLogger("pulsepipe.api")

app = FastAPI(
    title="PulsePipe Enterprise AI SDR Outbound Engine",
    description="Multi-channel sequence personalization, reply triage, CAN-SPAM compliance, 5-pool budget router, and deliverability health monitoring.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
@app.get("/health")
def healthz():
    return {"status": "healthy", "service": "pulsepipe-core-api", "version": "2.0.0", "simulate_mode": settings.SIMULATE}

@app.get("/readyz")
def readyz():
    return {"status": "ready", "engine": "sdr-personalizer-ready", "database": "sqlite-disk-connected"}

app.include_router(campaigns.router, prefix="/api/v1/campaigns", tags=["Outbound Campaigns"])
app.include_router(prospects.router, prefix="/api/v1/prospects", tags=["Prospect Targets"])
app.include_router(sequences.router, prefix="/api/v1/sequences", tags=["Sequence Orchestrator"])
app.include_router(inbox.router, prefix="/api/v1/inbox", tags=["Reply Triage Inbox"])
app.include_router(deliverability.router, prefix="/api/v1/deliverability", tags=["Deliverability Health"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["SHIVAM Admin Console"])
app.include_router(export.router, prefix="/api/v1/export", tags=["Exports"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.api.app.main:app", host="0.0.0.0", port=settings.API_PORT, reload=True)
