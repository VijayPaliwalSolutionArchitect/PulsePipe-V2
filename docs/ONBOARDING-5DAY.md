# 📅 PulsePipe V2 — 5-Day Engineer Onboarding Plan

**Document Version:** 2.0.0 · **Date:** November 2026 · **Author:** Vijay Paliwal (Solution Architect & Lead Developer)

---

### Day 1: Environment Setup & Architecture Familiarization
- Clone repository, run `copy .env.example .env`.
- Execute `python -m pytest tests/ -v` and `python -m evals.run_evals`.
- Read [SYSTEM-ARCHITECTURE-AND-DIAGRAMS.md](file:///C:/Vijay-Projects/PulsePipe%20-%20V2/docs/SYSTEM-ARCHITECTURE-AND-DIAGRAMS.md).

### Day 2: Outbound SDR Personalization & Personas
- Inspect `services/sdr_engine/personalizer.py` and `services/common/db.py`.
- Create a custom SDR persona via the API and inspect generated copy.

### Day 3: Sequence Orchestrator & Dispatch Pipeline
- Review `services/orchestrator/sequence_manager.py` and cadence rules.
- Test suppression logic and verify that opt-out links prevent dispatch.

### Day 4: Reply Triage & Intent Classifier
- Study `services/reply_triage/classifier.py`.
- Add test inbound emails and verify triage badge rendering in the React UI (`http://localhost:5175/inbox`).

### Day 5: Deliverability Health & Production Deployment
- Review SPF, DKIM, and DMARC verification in `services/api/app/routers/deliverability.py`.
- Deploy .NET gateway or run production Docker build.
