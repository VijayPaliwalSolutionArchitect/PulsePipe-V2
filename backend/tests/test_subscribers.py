"""Subscriber registration tests."""

from __future__ import annotations


def test_add_and_list_subscribers(client):
    client.post("/api/pipelines", json={"name": "with-subs"})
    pid = client.get("/api/pipelines/by-name/with-subs").json()["id"]

    resp = client.post(f"/api/pipelines/{pid}/subscribers",
                       json={"name": "zapier", "endpoint": "https://hooks.example.invalid/x"})
    assert resp.status_code == 201
    sub = resp.json()
    assert sub["pipeline_id"] == pid

    listed = client.get(f"/api/pipelines/{pid}/subscribers").json()
    assert any(s["id"] == sub["id"] for s in listed)


def test_subscriber_on_missing_pipeline_404(client):
    resp = client.post("/api/pipelines/9999/subscribers",
                       json={"name": "x", "endpoint": "http://x.invalid"})
    assert resp.status_code == 404


def test_delete_subscriber(client):
    client.post("/api/pipelines", json={"name": "del-subs"})
    pid = client.get("/api/pipelines/by-name/del-subs").json()["id"]
    sub = client.post(f"/api/pipelines/{pid}/subscribers",
                      json={"name": "gone", "endpoint": "http://x.invalid"}).json()
    assert client.delete(f"/api/subscribers/{sub['id']}").status_code == 204
    assert client.delete(f"/api/subscribers/{sub['id']}").status_code == 404


def test_subscriber_count_reflected_on_pipeline(client):
    client.post("/api/pipelines", json={"name": "counted"})
    pid = client.get("/api/pipelines/by-name/counted").json()["id"]
    client.post(f"/api/pipelines/{pid}/subscribers", json={"name": "s1", "endpoint": "http://x.invalid"})
    row = client.get(f"/api/pipelines/{pid}").json()
    assert row["subscriber_count"] == 1