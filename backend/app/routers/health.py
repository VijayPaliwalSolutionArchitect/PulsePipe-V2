"""Health, readiness and a small /echo helper.

``/api/health`` verifies that the database is reachable and is what a load
balancer or uptime monitor should probe.  ``/api/echo`` returns whatever body
it receives with HTTP 200 — it exists so demo pipelines seeded in the repo can
point subscribers at it and observe real end-to-end delivery without standing
up an external webhook receiver.
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import get_db
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service health, confirming the database is reachable."""
    db_ok = "ok"
    try:
        get_db().connect().execute("SELECT 1")
    except Exception:
        db_ok = "unavailable"
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.version,
        database=db_ok,
    )


@router.post("/echo")
async def echo(request: Request) -> JSONResponse:
    """Echo the request body back with HTTP 200.

    Used as a no-op subscriber endpoint for the seeded demo pipelines.
    """
    try:
        body = await request.json()
    except Exception:
        body = {"raw": (await request.body()).decode("utf-8", "replace")}
    return JSONResponse({"received": body, "pulsepipe": settings.app_name})