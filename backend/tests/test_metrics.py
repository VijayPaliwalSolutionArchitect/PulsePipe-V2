"""Metrics endpoint tests."""

from __future__ import annotations


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["version"]  # non-empty


def test_counts_and_throughput_empty(client):
    counts = client.get("/api/metrics/counts").json()
    assert counts["total_events"] == 0

    tp = client.get("/api/metrics/throughput?window_seconds=60").json()
    assert tp["events"] == 0


def test_counts_after_ingest(client, echo_server):
    client.post("/api/pipelines", json={"name": "m"})
    pid = client.get("/api/pipelines/by-name/m").json()["id"]
    client.post(f"/api/pipelines/{pid}/subscribers",
                json={"name": "echo", "endpoint": echo_server})
    for i in range(3):
        client.post("/api/events", json={"pipeline": "m", "payload": {"i": i}})

    counts = client.get("/api/metrics/counts").json()
    assert counts["total_events"] == 3
    assert counts["pipelines"][0]["events"] == 3

    tp = client.get("/api/metrics/throughput?window_seconds=3600").json()
    assert tp["events"] == 3

    queue = client.get("/api/metrics/queue").json()
    assert queue["total_depth"] == 0  # all emitted


def test_latency_after_emitted_events(client, echo_server):
    client.post("/api/pipelines", json={"name": "latency-pipe"})
    pid = client.get("/api/pipelines/by-name/latency-pipe").json()["id"]
    client.post(f"/api/pipelines/{pid}/subscribers",
                json={"name": "echo", "endpoint": echo_server})
    client.post("/api/events", json={"pipeline": "latency-pipe", "payload": {"x": 1}})

    lat = client.get("/api/metrics/latency").json()
    assert lat["emitted_events"] == 1
    assert lat["avg_latency_ms"] >= 0