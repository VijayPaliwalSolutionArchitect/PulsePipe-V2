from fastapi import APIRouter
from pydantic import BaseModel
from services.common.db import db

router = APIRouter()


class ReplyActionRequest(BaseModel):
    action: str
    reply_text: str


@router.get("/")
def list_inbox_replies(tenant_id: str = "acme-sales"):
    return db.get_replies(tenant_id)


@router.post("/{reply_id}/action")
def process_reply_action(reply_id: str, req: ReplyActionRequest, tenant_id: str = "acme-sales"):
    cur = db._conn.cursor()
    cur.execute("UPDATE replies SET status = 'processed', suggested_reply = ? WHERE id = ? AND tenant_id = ?", (req.reply_text, reply_id, tenant_id))
    db._conn.commit()
    return {"status": "processed", "reply_id": reply_id, "action": req.action}
