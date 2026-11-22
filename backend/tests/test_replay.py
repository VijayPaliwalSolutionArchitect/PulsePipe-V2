"""Replay endpoint tests."""

from __future__ import annotations


def test_replay_by_event_id(client, echo_server):
    client.post("/api/pipelines", json={"name": "rp"})
    pid = client.get("/api/pipelines/by-name/rp").json()["id"]
    client.post(f"/api/pipelines/{pid}/subscribers",
                json={"name": "echo", "endpoint": echo_server})

    ev = client.post("/api/events", json={"pipeline": "rp", "payload": {"k": "v"}}).json()
    res = client.post("/api/replay", json={"event_id": ev["event_id"]})
    assert res.status_code == 200
    body = res.json()
    assert body["events_selected"] == 1
    assert body["deliveries"] >= 1
    assert body["failures"] == 0


def test_replay_by_limit(client, echo_server):
    client.post("/api/pipelines", json={"name": "rpl"})
    pid = client.get("/api/pipelines/by-name/rpl").json()["id"]
    client.post(f"/api/pipelines/{pid}/subscribers",
                json={"name": "echo", "endpoint": echo_server})
    for i in range(4):
        client.post("/api/events", json={"pipeline": "rpl", "payload": {"i": i}})

    res = client.post("/api/replay", json={"limit": 2}).json()
    assert res["events_selected"] == 2
    assert res["deliveries"] == 2


def test_replay_unknown_event_zero_selected(client):
    res = client.post("/api/replay", json={"event_id": "does-not-exist"})
    assert res.status_code == 200
    assert res.json()["events_selected"] == 0