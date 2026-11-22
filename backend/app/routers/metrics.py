"""Metrics endpoints: throughput, counts, latency and queue depth."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas import (
    CountsResponse,
    LatencyResponse,
    QueueResponse,
    ThroughputResponse,
)
from app.services import metrics as svc

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/throughput", response_model=ThroughputResponse)
def throughput(window_seconds: int = Query(60, ge=1, le=86400)) -> dict:
    """Events per second over the last ``window_seconds``."""
    return svc.throughput(window_seconds=window_seconds)


@router.get("/counts", response_model=CountsResponse)
def counts() -> dict:
    """Total events plus per-pipeline breakdown."""
    return svc.counts()


@router.get("/latency", response_model=LatencyResponse)
def latency() -> dict:
    """Receive-to-emit latency in ms across emitted events."""
    return svc.latency()


@router.get("/queue", response_model=QueueResponse)
def queue() -> dict:
    """Depth of received-but-not-yet-emitted events per pipeline."""
    return svc.queue_depth()