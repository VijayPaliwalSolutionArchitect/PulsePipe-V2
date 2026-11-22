"""PulsePipe application entrypoint.

Run with either::

    uvicorn main:app --reload     # from the backend/ directory
    python main.py                # convenience wrapper

The app factory :func:`create_app` wires up CORS, the API routers under the
``/api`` prefix, first-boot seeding, and serves the static dashboard from the
project's ``frontend/`` directory at ``/``.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import get_db
from app.routers import alerts as alerts_router
from app.routers import events as events_router
from app.routers import health as health_router
from app.routers import metrics as metrics_router
from app.routers import pipelines as pipelines_router
from app.routers import replay as replay_router
from app.routers import subscribers as subscribers_router
from app.seed import seed

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Seed the demo data on first boot, then hand off to the server."""
    if settings.seed_on_start:
        seed(get_db())
    yield


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description=(
            "PulsePipe — a real-time event-streaming and observability "
            "pipeline. Ingest REST events, transform them on named pipelines, "
            "dispatch to subscribers, and observe throughput, latency, alerts "
            "and replays."
        ),
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for r in (
        health_router.router,
        pipelines_router.router,
        subscribers_router.router,
        events_router.router,
        metrics_router.router,
        alerts_router.router,
        replay_router.router,
    ):
        app.include_router(r, prefix="/api")

    # Serve the pre-built frontend dashboard as static files from the root.
    if settings.frontend_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(settings.frontend_dir), html=True), name="frontend")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )