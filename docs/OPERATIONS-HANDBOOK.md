# ⚙️ PulsePipe V2 — Operations Handbook

**Document Version:** 2.0.0 · **Date:** November 2026 · **Author:** Vijay Paliwal (Solution Architect & Lead Developer)

---

## 1. Outbound Mailbox Warm-Up & Reputation Management

PulsePipe V2 strictly enforces an automated warm-up curve to prevent domain blacklisting by major ESPs (Google Workspace, Microsoft 365):

| Warm-Up Stage | Daily Send Limit per Domain | Target Engagement Rate | Action on Bounce > 2% |
| :--- | :--- | :--- | :--- |
| **Week 1** | 10 emails / day | Zero hard bounces | Instant pause, verify DNS SPF/DKIM |
| **Week 2** | 25 emails / day | $\ge 20\%$ open rate | Review subject line spam-triggers |
| **Week 3** | 50 emails / day | $\ge 5\%$ reply rate | Safe for full production sequences |
| **Full Throttle** | 100 emails / day (per IP/mailbox) | $\ge 8\%$ reply rate | Rotate across multiple sending domains |

---

## 2. CAN-SPAM, GDPR & DPDP 2023 Compliance Operations

### 2.1 The Unsubscribe Lifecycle
1. Prospect clicks `"Unsubscribe here"` link in the email footer.
2. Inbound webhook or direct HTTP endpoint receives the request.
3. System verifies prospect token and commits email to the `suppressions` table.
4. An automated confirmation event is logged in `query_audit_logs`.
5. Future sequence steps check `suppressions` before dispatch; if present, dispatch is aborted with `status: "suppressed_opt_out"`.

### 2.2 PII Redaction
- Indian PAN (`[A-Z]{5}[0-9]{4}[A-Z]`), Aadhaar (12 digits), and US SSN (`\d{3}-\d{2}-\d{4}`) are automatically masked as `[REDACTED_PII]` by `guardrails/core.py`.
