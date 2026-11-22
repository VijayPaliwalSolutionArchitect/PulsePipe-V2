"""Alert rule CRUD and rule evaluation routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.database import get_db
from app.schemas import (
    AlertEvaluateResponse,
    AlertOut,
    AlertRuleCreate,
    AlertRuleOut,
)
from app.services import alerts as svc

router = APIRouter(tags=["alerts"])


@router.get("/alert-rules", response_model=list[AlertRuleOut])
def list_rules() -> list[dict]:
    """List all alert rules, newest first."""
    return svc.list_rules()


@router.post("/alert-rules", response_model=AlertRuleOut, status_code=201)
def create_rule(data: AlertRuleCreate) -> dict:
    """Create an alert rule (keyword or threshold)."""
    config: dict = {"severity": data.severity}
    if data.rule_type == "keyword":
        if not data.keyword:
            raise HTTPException(status_code=422, detail="keyword is required for keyword rules")
        config["keyword"] = data.keyword
    else:  # threshold
        if data.threshold is None:
            raise HTTPException(status_code=422, detail="threshold is required for threshold rules")
        config["threshold"] = data.threshold
        config["window_seconds"] = data.window_seconds
    try:
        return svc.create_rule(
            name=data.name,
            rule_type=data.rule_type,
            pipeline_id=data.pipeline_id,
            config=config,
            enabled=data.enabled,
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="pipeline not found")


@router.post("/alerts/evaluate", response_model=AlertEvaluateResponse)
def evaluate() -> dict:
    """Evaluate every enabled rule against stored events; persist fired alerts."""
    return svc.evaluate_rules()


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(limit: int = Query(50, ge=1, le=1000)) -> list[dict]:
    """Return fired alerts, newest first."""
    return svc.list_alerts(limit=limit)


@router.delete("/alert-rules/{rule_id}", status_code=204)
def delete_rule(rule_id: int) -> None:
    """Delete an alert rule."""
    db = get_db()
    db.execute("DELETE FROM alert_rules WHERE id = ?", (rule_id,))