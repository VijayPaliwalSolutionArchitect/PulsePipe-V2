import csv
import io
from fastapi import APIRouter, Response
from services.common.db import db

router = APIRouter()


@router.get("/prospects/csv")
def export_prospects_csv(tenant_id: str = "acme-sales"):
    prospects = db.get_prospects(tenant_id=tenant_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "First Name", "Last Name", "Email", "Company", "Title", "Industry", "Status", "Reply Intent"])

    for p in prospects:
        writer.writerow([
            p["id"], p["first_name"], p["last_name"], p["email"],
            p["company_name"], p["title"], p["industry"], p["status"],
            p.get("reply_intent") or "none"
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=pulsepipe_prospects_{tenant_id}.csv"}
    )
