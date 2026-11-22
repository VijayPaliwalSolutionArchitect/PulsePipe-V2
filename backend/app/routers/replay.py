"""Replay endpoint: re-emit stored events to subscribers."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas import ReplayRequest, ReplayResult
from app.services import replay as svc

router = APIRouter(prefix="/replay", tags=["replay"])


@router.post("", response_model=ReplayResult)
def replay(data: ReplayRequest) -> dict:
    """Re-emit events selected by ``event_id``, a time window or a limit."""
    return svc.replay(data)