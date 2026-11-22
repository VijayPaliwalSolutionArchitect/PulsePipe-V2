"""Subscriber registration routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import SubscriberCreate, SubscriberOut
from app.services import subscribers as svc

router = APIRouter(tags=["subscribers"])


@router.get("/pipelines/{pipeline_id}/subscribers", response_model=list[SubscriberOut])
def list_subscribers(pipeline_id: int) -> list[dict]:
    """List all subscribers registered on a pipeline."""
    return svc.list_subscribers(pipeline_id)


@router.post("/pipelines/{pipeline_id}/subscribers", response_model=SubscriberOut, status_code=201)
def add_subscriber(pipeline_id: int, data: SubscriberCreate) -> dict:
    """Register a subscriber; 404 if the pipeline does not exist."""
    try:
        return svc.create_subscriber(pipeline_id, data)
    except LookupError:
        raise HTTPException(status_code=404, detail="pipeline not found")


@router.delete("/subscribers/{subscriber_id}", status_code=204)
def remove_subscriber(subscriber_id: int) -> None:
    """Remove a subscriber; 404 if it does not exist."""
    if not svc.delete_subscriber(subscriber_id):
        raise HTTPException(status_code=404, detail="subscriber not found")