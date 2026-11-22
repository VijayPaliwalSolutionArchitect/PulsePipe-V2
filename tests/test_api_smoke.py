def test_healthz_and_readyz(client):
    r1 = client.get("/healthz")
    assert r1.status_code == 200
    assert r1.json()["status"] == "healthy"

    r2 = client.get("/readyz")
    assert r2.status_code == 200

def test_campaigns_and_prospects_list(client):
    c = client.get("/api/v1/campaigns/")
    assert c.status_code == 200
    assert len(c.json()) >= 1

    p = client.get("/api/v1/prospects/")
    assert p.status_code == 200
    assert len(p.json()) >= 3

def test_inbox_and_deliverability_health(client):
    i = client.get("/api/v1/inbox/")
    assert i.status_code == 200
    assert len(i.json()) >= 2

    d = client.get("/api/v1/deliverability/health")
    assert d.status_code == 200
    assert d.json()["dns_records"]["spf"]["status"] == "PASS"

def test_admin_stats_and_settings(client):
    s = client.get("/api/v1/admin/stats")
    assert s.status_code == 200
    assert s.json()["active_campaigns"] >= 1
