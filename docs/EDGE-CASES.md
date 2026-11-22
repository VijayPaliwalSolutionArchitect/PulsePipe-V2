# ⚠️ PulsePipe V2 — Edge Cases & Failure Mitigation

**Document Version:** 2.0.0 · **Date:** November 2026 · **Author:** Vijay Paliwal (Solution Architect & Lead Developer)

---

## 1. Edge Case Handling Matrix

| Scenario | Edge Condition | System Behavior |
| :--- | :--- | :--- |
| **Opt-Out During Active Sequence** | Prospect replies *"unsubscribe"* during Step 1. | Reply triage instantly marks intent as `unsubscribe`, inserts email into `suppressions`, and cancels Step 2 and Step 3. |
| **Out of Office Reply** | Prospect autoreply: *"Traveling until next Monday"*. | Intent classified as `out_of_office`. Sequence delay paused for 7 days rather than firing subsequent steps into an unmonitored inbox. |
| **Malformed Prospect Data** | Missing tech stack or company name. | System falls back to high-level industry challenge templates rather than emitting placeholder syntax like `{{company}}`. |
| **Budget Hard Cap Exceeded** | Tenant exceeds monthly $150 cap. | Model Router shifts from commercial API to `offline/local` Ollama model; outbound cadence continues without billing spikes. |
