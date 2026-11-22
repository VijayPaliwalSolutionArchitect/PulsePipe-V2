# 🧪 PulsePipe V2 — Testing & Quality Assurance Handbook

**Document Version:** 2.0.0 · **Date:** November 2026 · **Author:** Vijay Paliwal (Solution Architect & Lead Developer)

---

## 1. Test Architecture Overview

PulsePipe V2 maintains 100% test pass rates across unit, integration, and release eval tiers:

1. **API Smoke Tests (`tests/test_api_smoke.py`):** Health probes (`/healthz`, `/readyz`), campaign listing, prospect retrieval.
2. **SDR Personalizer Tests (`tests/test_sdr_personalizer.py`):** Validates that generated copy includes prospect company, tech stack, and physical address.
3. **Reply Classifier Tests (`tests/test_reply_classifier.py`):** Validates precision across `interested`, `more_info`, `out_of_office`, and `unsubscribe`.
4. **CAN-SPAM Compliance Tests (`tests/test_can_spam_compliance.py`):** Ensures emails lacking physical address or opt-out tokens are strictly rejected.
5. **Sequence Orchestrator Tests (`tests/test_sequence_orchestrator.py`):** Confirms suppressed emails are never dispatched.
6. **Hard Evals Gate (`tests/test_evals_gate.py`):** Automated blocker verifying all golden criteria.
