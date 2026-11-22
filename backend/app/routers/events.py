"""Event ingest and read routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas import EventIngest, EventOut
from app.services import events as svc

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventOut, status_code=201)
def ingest(data: EventIngest) -> dict:
    """Ingest one event into a named pipeline.

    The event is deduplicated on ``event_id``, transformed, stored, and
    dispatched to the pipeline's subscribers (see ``services/events.py``).
    A repeated ``event_id`` returns the stored event with ``dedup=true`` and
    does not dispatch again.
    """
    try:
        stored, results, is_dedup = svc.ingest(data)
    except LookupError:
        raise HTTPException(status_code=404, detail=f"pipeline '{data.pipeline}' not found")

    # Attach a light-weight dispatch summary for observability so callers can
    # see delivery outcomes without a separate round-trip.
    stored["emit"] = [
        {
            "subscriber_id": r.subscriber_id,
            "subscriber_name": r.subscriber_name,
            "endpoint": r.endpoint,
            "ok": r.ok,
            "detail": r.detail,
        }
        for r in results
    ]
    stored["dedup"] = bool(is_dedup or stored.get("dedup"))
    return stored


@router.get("", response_model=list[EventOut])
def list_events(
    pipeline_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=1000),
) -> list[dict]:
    """List stored events, newest first, optionally filtered by pipeline."""
    return svc.list_events(pipeline_id=pipeline_id, limit=limit)


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int) -> dict:
    """Return a single stored event, or 404."""
    row = svc.get_event(event_id)
    if row is None:
        raise HTTPException(status_code=404, detail="event not found")
    return row