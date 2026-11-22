"""Event ingest, transform, dedup and dispatch tests."""

from __future__ import annotations
import uuid


def test_ingest_against_unknown_pipeline_404(client):
    resp = client.post("/api/events", json={"pipeline": "nope", "payload": {}})
    assert resp.status_code == 404


def test_ingest_applies_transforms_and_stores(client, echo_server):
    resp = client.post(
        "/api/pipelines",
        json={"name": "webhooks", "transform_spec": ["normalize:email", "tag:inbound", "extract:src:origin"]},
    )
    assert resp.status_code == 201
    pid = resp.json()["id"]
    client.post(f"/api/pipelines/{pid}/subscribers",
                json={"name": "echo", "endpoint": echo_server})

    ingest = client.post("/api/events", json={
        "pipeline": "webhooks",
        "payload": {"email": "  A@B.COM ", "src": "salesforce"},
    })
    assert ingest.status_code == 201, ingest.text
    body = ingest.json()
    assert body["payload"]["email"] == "a@b.com"          # normalized
    assert "inbound" in body["payload"]["tags"]           # tagged
    assert body["payload"]["origin"] == "salesforce"      # extracted
    assert body["status"] == "emitted"                    # dispatched to echo
    assert all(r["ok"] for r in body["emit"])
    assert not body["dedup"]


def test_ingest_dedup_does_not_resend(client, echo_server):
    client.post("/api/pipelines", json={"name": "uniq"})
    pid = client.get("/api/pipelines/by-name/uniq").json()["id"]
    client.post(f"/api/pipelines/{pid}/subscribers",
                json={"name": "echo", "endpoint": echo_server})

    key = "evt-" + uuid.uuid4().hex
    first = client.post("/api/events", json={"pipeline": "uniq", "event_id": key, "payload": {"x": 1}})
    second = client.post("/api/events", json={"pipeline": "uniq", "event_id": key, "payload": {"x": 2}})
    assert first.status_code == second.status_code == 201
    assert second.json()["dedup"] is True
    assert second.json()["payload"] == {"x": 1}  # original stored payload kept

    events = client.get("/api/events").json()
    matching = [e for e in events if e["event_id"] == key]
    assert len(matching) == 1


def test_list_and_get_event(client, echo_server):
    client.post("/api/pipelines", json={"name": "listing"})
    pid = client.get("/api/pipelines/by-name/listing").json()["id"]
    client.post(f"/api/pipelines/{pid}/subscribers",
                json={"name": "echo", "endpoint": echo_server})
    created = client.post("/api/events", json={"pipeline": "listing", "payload": {"a": 1}}).json()

    listing = client.get("/api/events").json()
    assert any(e["id"] == created["id"] for e in listing)
    single = client.get(f"/api/events/{created['id']}")
    assert single.status_code == 200 and single.json()["event_id"] == created["event_id"]
    assert client.get("/api/events/99999").status_code == 404


def test_emit_failure_is_reported(client):
    client.post("/api/pipelines", json={"name": "deadhost"})
    pid = client.get("/api/pipelines/by-name/deadhost").json()["id"]
    client.post(f"/api/pipelines/{pid}/subscribers",
                json={"name": "dead", "endpoint": "http://127.0.0.1:1/none"})
    body = client.post("/api/events", json={"pipeline": "deadhost", "payload": {"x": 1}}).json()
    assert body["status"] == "failed"
    assert body["emit"][0]["ok"] is False