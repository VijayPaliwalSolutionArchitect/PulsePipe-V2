"""Seed the database with demo pipelines, alert rules and sample events.

Runs on first boot (when ``PULSEPIPE_SEED_ON_START`` is true and the
``pipelines`` table is empty) so a freshly-cloned repo is usable out of the
box: the dashboard has something to show and the demo ingest journey works
end-to-end against the app's own ``/api/echo`` subscriber.

The seed is idempotent — if any pipelines already exist, nothing is written.
Demo events are inserted *directly* into the ``events`` table rather than sent
through :func:`app.services.events.ingest`, because calling the live dispatch
path during app startup would POST to our own not-yet-accepting socket and
block until the HTTP timeout.  They are stored with status ``received`` and
can be replayed or dispatched later via the API once the server is up.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from app.database import Database, get_db
from app.schemas import PipelineCreate, SubscriberCreate
from app.services import alerts as alerts_svc
from app.services import pipelines as pipeline_svc
from app.services import subscribers as subscriber_svc

log = logging.getLogger(__name__)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# A demo event with a couple of interesting signals for the alert rules.
_DEMO_EVENTS = [
    {
        "event_id": "demo-webhook-001",
        "pipeline": "webhook-ingest",
        "payload": {
            "source": "salesforce.trailhead",
            "contact": "ada@acme-corp.example",
            "tier": "enterprise",
        },
    },
    {
        "event_id": "demo-webhook-002",
        "pipeline": "webhook-ingest",
        "payload": {
            "source": "hubspot.form",
            "contact": "grace@northwind.example",
            "tier": "midmarket",
        },
    },
    {
        "event_id": "demo-order-001",
        "pipeline": "order-events",
        "payload": {"order_id": "ORD-4412", "amount": 129.0, "error": False},
    },
]


def seed(db: Optional[Database] = None) -> bool:
    """Populate demo pipelines / rules / events. Returns True if it seeded."""
    db = db or get_db()
    if db.query_one("SELECT COUNT(*) AS n FROM pipelines")["n"] > 0:
        return False

    pipelines = [
        PipelineCreate(
            name="webhook-ingest",
            description="Ingest + enrich inbound webhook events.",
            source="scoutforge",
            transform_spec=[
                "normalize:contact",
                "tag:inbound",
                "extract:source:origin",
            ],
            sinks=["webhooks"],
        ),
        PipelineCreate(
            name="order-events",
            description="Order lifecycle events with volume alerting.",
            source="checkout",
            transform_spec=["drop:raw", "add:environment:prod"],
            sinks=["erp"],
        ),
        PipelineCreate(
            name="clickstream",
            description="Unfiltered clickstream with a keyword error-rule.",
            source="analytics",
            transform_spec=["tag:click"],
            sinks=["warehouse"],
        ),
    ]
    for p in pipelines:
        row = pipeline_svc.create_pipeline(p, db)
        # Subscribe each demo pipeline to the app's own echo endpoint so the
        # end-to-end delivery demo works without any external receiver.
        subscriber_svc.create_subscriber(
            row["id"],
            SubscriberCreate(
                name=f"{p.name}-echo",
                endpoint="http://127.0.0.1:8000/api/echo",
            ),
            db,
        )

    # Alert rules: one keyword rule catching "error" on clickstream, one
    # volume-threshold rule on order-events.
    click_id = pipeline_svc.find_by_name("clickstream", db)["id"]
    order_id = pipeline_svc.find_by_name("order-events", db)["id"]
    alerts_svc.create_rule("error-keyword", "keyword", click_id, {"keyword": "error"}, db=db)
    alerts_svc.create_rule(
        "order-spike",
        "threshold",
        order_id,
        {"threshold": 5, "window_seconds": 60, "severity": "critical"},
        db=db,
    )

    # Insert demo events directly (see module docstring re: startup dispatch).
    for ev in _DEMO_EVENTS:
        pipe = pipeline_svc.find_by_name(ev["pipeline"], db)
        if pipe is None:
            log.warning("seed skip: pipeline %r missing", ev["pipeline"])
            continue
        db.execute(
            "INSERT INTO events (event_id, pipeline_id, payload, received_at, status, dedup) "
            "VALUES (?, ?, ?, ?, 'received', 0)",
            (ev["event_id"], pipe["id"], db.dumps(ev["payload"]), _utcnow()),
        )

    log.info(
        "seeded %d pipelines, 2 alert rules, %d demo events",
        len(pipelines), len(_DEMO_EVENTS),
    )
    return True