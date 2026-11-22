# 🌊 PulsePipe V2 — Technical Flowcharts & Sequence Logic

**Document Version:** 2.0.0 · **Date:** November 2026 · **Author:** Vijay Paliwal (Solution Architect & Lead Developer)

---

## 1. End-to-End SDR Sequence Flow

```mermaid
sequenceDiagram
    autonumber
    actor SDR as SDR Operator
    participant UI as PulsePipe Web Console (5175)
    participant API as FastAPI Backend (8093)
    participant LLM as 5-Pool Budget Router
    participant DB as SQLite / Postgres Store
    participant ESP as Sending Mailbox (Mailgun/SES)
    actor Prospect as Target Prospect

    SDR->>UI: Select Prospect (e.g. Sarah Chen)
    UI->>API: POST /v1/sequences/generate-copy
    API->>LLM: Synthesize Tech Stack & Signals
    LLM-->>API: Personalized Subject & Body + CAN-SPAM Footer
    API-->>UI: Display Generated Copy Preview
    SDR->>UI: Approve & Dispatch
    UI->>API: POST /v1/sequences/dispatch
    API->>DB: Check Suppressions Blacklist
    Note over API,DB: If suppressed, abort with 400
    API->>ESP: Dispatch Email
    ESP->>Prospect: Deliver to Inbox
    Prospect->>API: Inbound Reply Received
    API->>LLM: Classify Intent (Interested / Unsub / etc)
    LLM-->>API: Reply Intent + Suggested Action
    API->>DB: Store in replies table
    API-->>UI: Surface in AI Reply Triage Inbox
```
