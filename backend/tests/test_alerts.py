"""Alert rule creation, evaluation and keyword/threshold firing tests."""

from __future__ import annotations


def _pipe(client, name):
    client.post("/api/pipelines", json={"name": name})
    return client.get(f"/api/pipelines/by-name/{name}").json()["id"]


def test_create_keyword_rule_and_fire(client, echo_server):
    pid = _pipe(client, "kw-pipe")
    client.post(f"/api/pipelines/{pid}/subscribers",
                json={"name": "echo", "endpoint": echo_server})
    client.post("/api/alert-rules", json={
        "pipeline_id": pid, "name": "catch-error",
        "rule_type": "keyword", "keyword": "error", "severity": "critical",
    })

    # clean event first
    client.post("/api/events", json={"pipeline": "kw-pipe", "payload": {"msg": "all good"}})
    client.post("/api/events", json={"pipeline": "kw-pipe", "payload": {"msg": "an error here"}})

    res = client.post("/api/alerts/evaluate")
    assert res.status_code == 200
    fired = [a for a in res.json()["alerts"] if a["message"].startswith("keyword 'error'")]
    assert len(fired) == 1
    assert fired[0]["severity"] == "critical"

    listed = client.get("/api/alerts").json()
    assert any(a["message"].startswith("keyword 'error'") for a in listed)


def test_threshold_rule_fires_on_volume(client):
    pid = _pipe(client, "vol-pipe")
    client.post("/api/alert-rules", json={
        "pipeline_id": pid, "name": "spike",
        "rule_type": "threshold", "threshold": 3, "window_seconds": 3600,
    })
    for i in range(3):
        client.post("/api/events", json={"pipeline": "vol-pipe", "payload": {"i": i}})

    res = client.post("/api/alerts/evaluate").json()
    assert res["rules_evaluated"] == 1
    assert any("threshold hit" in a["message"] for a in res["alerts"])


def test_threshold_rule_does_not_fire_below_limit(client):
    pid = _pipe(client, "quiet-pipe")
    client.post("/api/alert-rules", json={
        "pipeline_id": pid, "name": "mini",
        "rule_type": "threshold", "threshold": 10, "window_seconds": 3600,
    })
    client.post("/api/events", json={"pipeline": "quiet-pipe", "payload": {}})
    res = client.post("/api/alerts/evaluate").json()
    assert res["alerts_fired"] == 0


def test_validation(client):
    # keyword rule without a keyword is 422
    r = client.post("/api/alert-rules", json={
        "pipeline_id": None, "name": "bad", "rule_type": "keyword",
    })
    assert r.status_code == 422

    # threshold rule on a missing pipeline is 404
    r = client.post("/api/alert-rules", json={
        "pipeline_id": 9999, "name": "bad", "rule_type": "threshold", "threshold": 2,
    })
    assert r.status_code == 404


def test_delete_rule(client):
    pid = _pipe(client, "del-rule")
    rule = client.post("/api/alert-rules", json={
        "pipeline_id": pid, "name": "tmp", "rule_type": "keyword", "keyword": "x",
    }).json()
    assert client.delete(f"/api/alert-rules/{rule['id']}").status_code == 204
    rules = client.get("/api/alert-rules").json()
    assert all(r["id"] != rule["id"] for r in rules)