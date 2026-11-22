# 🔍 PulsePipe V2 — Troubleshooting & Triage Handbook

**Document Version:** 2.0.0 · **Date:** November 2026 · **Author:** Vijay Paliwal (Solution Architect & Lead Developer)

---

## 1. Common Issues & Fast Triage Playbooks

### Issue 1: Outbound Email Dispatch Aborted with "Suppressed Recipient"
- **Cause:** The prospect's email address exists in the `suppressions` blacklist (either due to a previous opt-out or manual administrative block).
- **Resolution:**
  1. Inspect suppression status: `GET /api/v1/admin/suppressions?tenant_id=acme-sales`.
  2. If the opt-out was requested by the user, **DO NOT REMOVE** (compliance violation).
  3. If suppression was added mistakenly, remove via `DELETE /api/v1/admin/suppressions/{id}`.

### Issue 2: Evals Gate Failure on Release Build
- **Cause:** One of the release criteria in `evals/run_evals.py` fell below the hard threshold (e.g. Reply Intent Accuracy < 90% or missing CAN-SPAM footer).
- **Resolution:**
  1. Run evals directly: `python -m evals.run_evals`.
  2. Review failed assertions in the console output.
  3. Ensure `services/compliance/can_spam.py` footer validation passes on all generated copies.
  4. Ensure keyword triggers in `ReplyTriageClassifier` cover the edge case.

### Issue 3: Port Conflict on Startup
- **Port 8093:** FastAPI backend. If occupied, locate process: `Get-NetTCPConnection -LocalPort 8093` and terminate.
- **Port 5175:** Vite frontend dev server.
