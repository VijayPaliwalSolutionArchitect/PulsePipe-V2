# 📖 PulsePipe V2 — Operations & Incident Runbooks

**Document Version:** 2.0.0 · **Date:** November 2026 · **Author:** Vijay Paliwal (Solution Architect & Lead Developer)

---

## Runbook 1: Emergency Cadence Pause (Domain Reputation Safeguard)
**Trigger:** Spike in bounce rate (> 2%) or sudden ESP throttle.
**Steps:**
1. Navigate to `http://localhost:5175/deliverability`.
2. Review current bounce count and domain send volume.
3. Call `PATCH /api/v1/campaigns/{id}` with `{"status": "paused"}`.
4. Verify outbox dispatch terminates immediately.

## Runbook 2: Manual Compliance Blacklist Injection
**Trigger:** A corporate domain requests domain-wide opt-out.
**Steps:**
1. Open `http://localhost:5175/admin/suppressions`.
2. Enter wildcard or target email: `*@targetdomain.com` or specific address.
3. Click **"Add to Blacklist"**.
4. Confirm entry appears in the suppression table.
