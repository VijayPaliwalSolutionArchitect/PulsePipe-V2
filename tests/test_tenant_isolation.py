from services.common.db import db

def test_tenant_data_isolation():
    acme_prospects = db.get_prospects(tenant_id="acme-sales")
    saas_prospects = db.get_prospects(tenant_id="saas-growth")

    acme_ids = {p["id"] for p in acme_prospects}
    saas_ids = {p["id"] for p in saas_prospects}

    assert len(acme_ids.intersection(saas_ids)) == 0
    assert all(p["tenant_id"] == "acme-sales" for p in acme_prospects)
