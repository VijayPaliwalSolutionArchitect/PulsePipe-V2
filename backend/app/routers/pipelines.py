"""CRUD routes for named pipelines."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import PipelineCreate, PipelineOut, PipelineUpdate
from app.services import pipelines as svc

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


def _to_out(row: dict) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "source": row["source"],
        "transform_spec": row["transform_spec"],
        "sinks": row["sinks"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "event_count": row.get("event_count", 0),
        "subscriber_count": row.get("subscriber_count", 0),
    }


@router.get("", response_model=list[PipelineOut])
def list_pipelines() -> list[dict]:
    """List every pipeline with event/subscriber counts."""
    return [_to_out(row) for row in svc.list_pipelines()]


@router.get("/by-name/{name}", response_model=PipelineOut)
def get_pipeline_by_name(name: str) -> dict:
    """Look up a pipeline by its unique name."""
    row = svc.find_by_name(name)
    if row is None:
        raise HTTPException(status_code=404, detail=f"pipeline '{name}' not found")
    return _to_out(row)


@router.get("/{pipeline_id}", response_model=PipelineOut)
def get_pipeline(pipeline_id: int) -> dict:
    """Return a single pipeline, or 404."""
    row = svc.get_pipeline(pipeline_id)
    if row is None:
        raise HTTPException(status_code=404, detail="pipeline not found")
    return _to_out(row)


@router.post("", response_model=PipelineOut, status_code=201)
def create_pipeline(data: PipelineCreate) -> dict:
    """Create a pipeline; 409 on a duplicate name."""
    try:
        row = svc.create_pipeline(data)
    except ValueError:
        raise HTTPException(status_code=409, detail=f"pipeline '{data.name}' already exists")
    return _to_out(row)


@router.patch("/{pipeline_id}", response_model=PipelineOut)
def update_pipeline(pipeline_id: int, data: PipelineUpdate) -> dict:
    """Patch a pipeline's fields; 404 if it does not exist."""
    row = svc.update_pipeline(pipeline_id, data)
    if row is None:
        raise HTTPException(status_code=404, detail="pipeline not found")
    return _to_out(row)


@router.delete("/{pipeline_id}", status_code=204)
def delete_pipeline(pipeline_id: int) -> None:
    """Delete a pipeline (cascades to events, subscribers and alerts)."""
    if not svc.delete_pipeline(pipeline_id):
        raise HTTPException(status_code=404, detail="pipeline not found")