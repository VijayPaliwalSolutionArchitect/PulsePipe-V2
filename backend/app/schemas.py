"""Pydantic request/response schemas for the PulsePipe HTTP API.

Keeping the wire model separate from the SQLite storage layer lets the API
shape evolve independently of the schema.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.utcnow().isoformat() + "Z"


# ---------------------------------------------------------------------------
# Ping / health
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    """Result of a GET /api/health probe."""

    status: str = "ok"
    app: str
    version: str
    database: str
    time: str = Field(default_factory=_now_iso)


# ---------------------------------------------------------------------------
# Pipelines
# ---------------------------------------------------------------------------
class PipelineCreate(BaseModel):
    """Payload used to create a pipeline."""

    name: str = Field(..., min_length=1, max_length=120, description="Unique name")
    description: str = ""
    source: str = Field("", description="Origin label, e.g. 'webhook'")
    transform_spec: list[str] = Field(
        default_factory=list, description="Ordered transform rules (keywords)"
    )
    sinks: list[str] = Field(
        default_factory=list, description="Subscriber endpoint URLs"
    )


class PipelineUpdate(BaseModel):
    """Optional fields that may be patched on an existing pipeline."""

    description: Optional[str] = None
    source: Optional[str] = None
    transform_spec: Optional[list[str]] = None
    sinks: Optional[list[str]] = None


class PipelineOut(BaseModel):
    """Serialized pipeline as returned by the API."""

    id: int
    name: str
    description: str = ""
    source: str = ""
    transform_spec: list[str] = Field(default_factory=list)
    sinks: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    event_count: int = 0
    subscriber_count: int = 0


# ---------------------------------------------------------------------------
# Subscribers
# ---------------------------------------------------------------------------
class SubscriberCreate(BaseModel):
    """Payload used to register a subscriber on a pipeline."""

    name: str = Field(..., min_length=1, max_length=120)
    endpoint: str = Field(..., min_length=1, description="HTTP(S) URL")


class SubscriberOut(BaseModel):
    """Serialized subscriber record."""

    id: int
    pipeline_id: int
    name: str
    endpoint: str
    created_at: str


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------
class EventIngest(BaseModel):
    """Payload posted to /events.

    ``event_id`` is deduplicated per pipeline; ``payload`` must be a JSON
    object. The event is timestamped at receipt with ``received_at``.
    """

    model_config = ConfigDict(validate_default=True)

    event_id: Optional[str] = Field(
        default=None,
        description="Client-supplied dedup key; a UUID is generated if omitted",
    )
    pipeline: str = Field(..., min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_id")
    @classmethod
    def _default_event_id(cls, v: Optional[str]) -> str:
        return v or str(uuid4())


class EventOut(BaseModel):
    """Serialized event, either stored or immediately emitted."""

    id: int
    event_id: str
    pipeline_id: int
    pipeline: str = ""
    payload: dict[str, Any]
    received_at: str
    emitted_at: Optional[str] = None
    status: str = "received"
    dedup: bool = False
    emit: list[EmitResult] = Field(
        default_factory=list,
        description="Per-subscriber delivery outcomes for this ingest",
    )


class EmitResult(BaseModel):
    """Outcome of delivering an event to a subscriber."""

    subscriber_id: int
    subscriber_name: str
    endpoint: str
    ok: bool
    detail: str = ""


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
class ThroughputResponse(BaseModel):
    """Events-per-second over the requested window."""

    window_seconds: int
    duration_seconds: float
    events: int
    events_per_second: float


class PipelineCount(BaseModel):
    """Per-pipeline event count."""

    pipeline_id: int
    pipeline: str
    events: int


class CountsResponse(BaseModel):
    """Aggregate event counts."""

    total_events: int
    pipelines: list[PipelineCount]


class LatencyResponse(BaseModel):
    """Average receive->emit latency in milliseconds."""

    emitted_events: int
    avg_latency_ms: float
    max_latency_ms: float
    min_latency_ms: float
    sample_period: str


class QueueResponse(BaseModel):
    """Per-pipeline queue depth (received-but-not-yet-emitted events)."""

    total_depth: int
    by_pipeline: list[PipelineCount]


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------
class AlertRuleCreate(BaseModel):
    """Payload used to create an alert rule.

    rule_type:
      - ``threshold``: fire when >= N events arrive within ``window_seconds``
      - ``keyword``:   fire when the event payload contains ``keyword``
    """

    pipeline_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=120)
    rule_type: str = Field(..., pattern="^(keyword|threshold)$")
    keyword: Optional[str] = None
    threshold: Optional[int] = Field(default=None, ge=1)
    window_seconds: int = Field(default=60, ge=1, le=86400)
    severity: str = Field(default="warning", pattern="^(info|warning|critical)$")
    enabled: bool = True


class AlertRuleOut(BaseModel):
    """Serialized alert rule."""

    id: int
    pipeline_id: int
    pipeline: str = ""
    name: str
    rule_type: str
    config: dict[str, Any]
    enabled: bool
    created_at: str


class AlertOut(BaseModel):
    """Serialized alert record."""

    id: int
    rule_id: int
    pipeline_id: int
    pipeline: str = ""
    severity: str
    message: str
    event_ids: list[str] = Field(default_factory=list)
    triggered_at: str


class AlertEvaluateResponse(BaseModel):
    """Result of evaluating all enabled alert rules."""

    rules_evaluated: int
    alerts_fired: int
    alerts: list[AlertOut]


# ---------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------
class ReplayRequest(BaseModel):
    """Describe which events should be re-emitted.

    Exactly one selector should be supplied:
      - ``event_id``  : a single event
      - ``window_from``/``window_to`` : all events in a time range
      - ``limit``     : the most recent N events (when neither is given)
    """

    event_id: Optional[str] = None
    window_from: Optional[str] = None  # ISO-8601
    window_to: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=1000)


class ReplayResult(BaseModel):
    """Outcome of a replay batch."""

    requested: str
    events_selected: int
    deliveries: int
    failures: int
    replayed_at: str = Field(default_factory=_now_iso)