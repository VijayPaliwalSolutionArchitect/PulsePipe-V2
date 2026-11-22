# 📋 PulsePipe V2 — Architecture & Design Questionnaire

**Document Version:** 2.0.0 · **Date:** November 2026 · **Author:** Vijay Paliwal (Solution Architect & Lead Developer)

---

### Q1: What differentiates PulsePipe V2 from generic cold outreach tools?
**Answer:** Generic tools send repetitive static templates that get flagged as spam. PulsePipe V2 dynamically generates consultative, peer-to-peer technical emails tailored to each prospect's specific engineering stack and hiring signals, triages incoming replies with automated sentiment/intent classification, and strictly guarantees 100% CAN-SPAM and GDPR compliance.

### Q2: How is multi-tenant isolation enforced?
**Answer:** Every table (`campaigns`, `prospects`, `sequences`, `replies`, `suppressions`) indexes `tenant_id`. FastAPI endpoints enforce tenant filtering on all queries, and the Evals Gate executes cross-tenant data bleed tests before release.

### Q3: How are LLM costs kept under control?
**Answer:** PulsePipe V2 utilizes a 5-Pool Dynamic Model Router. High-frequency classification tasks (reply triage) route to ultra-fast economy models, while complex email generation routes to balanced models. If a tenant hits their monthly budget cap, the router automatically falls back to an offline local model.
