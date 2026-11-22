"""Pipeline CRUD and transform/ingest integration tests."""

from __future__ import annotations


def _make_pipeline(client, name="orders", **kw):
    payload = {
        "name": name,
        "description": "test pipeline",
        "transform_spec": ["tag:t", "normalize:email"],
        "sinks": ["http://example.invalid"],
        **kw,
    }
    resp = client.post("/api/pipelines", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_and_list_pipeline(client):
    created = _make_pipeline(client)
    assert created["name"] == "orders"
    assert created["event_count"] == 0

    resp = client.get("/api/pipelines")
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()]
    assert "orders" in names


def test_duplicate_pipeline_409(client):
    _make_pipeline(client, name="dup")
    resp = client.post("/api/pipelines", json={"name": "dup"})
    assert resp.status_code == 409


def test_get_pipeline_by_name_and_id(client):
    row = _make_pipeline(client, name="branded")
    by_name = client.get("/api/pipelines/by-name/branded")
    assert by_name.status_code == 200 and by_name.json()["id"] == row["id"]
    missing = client.get("/api/pipelines/by-name/nope")
    assert missing.status_code == 404


def test_patch_pipeline(client):
    row = _make_pipeline(client, name="patchable")
    resp = client.patch(f"/api/pipelines/{row['id']}", json={"description": "updated"})
    assert resp.status_code == 200
    assert resp.json()["description"] == "updated"
    assert resp.json()["name"] == "patchable"  # unchanged fields preserved
    assert client.patch("/api/pipelines/9999", json={}).status_code == 404


def test_delete_pipeline(client):
    row = _make_pipeline(client, name="byebye")
    assert client.delete(f"/api/pipelines/{row['id']}").status_code == 204
    assert client.get(f"/api/pipelines/{row['id']}").status_code == 404
    assert client.delete(f"/api/pipelines/{row['id']}").status_code == 404


def test_missing_pipeline_404(client):
    assert client.get("/api/pipelines/9999").status_code == 404
    assert client.get("/api/pipelines/by-name/ghost").status_code == 404