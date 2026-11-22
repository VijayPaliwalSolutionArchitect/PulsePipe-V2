# ⚡ PulsePipe V2 — Capabilities & Features Handbook

**Document Version:** 2.0.0 · **Date:** November 2026 · **Author:** Vijay Paliwal (Solution Architect & Lead Developer)

---

## 1. Executive Summary & Value Proposition

PulsePipe V2 is an enterprise-grade, autonomous Outbound AI SDR (Sales Development Representative) and multi-channel sequence engine designed for B2B engineering and enterprise sales teams. Unlike generic cold-email sequencers, PulsePipe V2 synthesizes deep company signals (technology stacks, hiring triggers, executive public statements, and distributed infrastructure challenges) to generate hyper-personalized, peer-to-peer cold outreach that achieves industry-leading response rates while adhering to strict CAN-SPAM, GDPR, and DPDP 2023 compliance regulations.

---

## 2. Core Functional Capabilities

### 2.1 Autonomous Outbound SDR Personalization Engine
- **Signal-Grounded Writing:** Ingests prospect account intelligence (e.g. AWS, Kubernetes, gRPC, Rust microservices) and crafts consultative, peer-to-peer value propositions without robotic sales fluff.
- **Dynamic SDR Personas:** Configurable consultative styles (e.g., Peer Technical Architect vs. Enterprise Account Executive), custom tones, and domain positioning.
- **Adaptive Cadences:** Supports 3-step default sequences:
  1. *Step 1 (Signal-Personalized Intro):* Grounded in target tech stack and engineering hiring signals.
  2. *Step 2 (Technical Proof & Value):* Benchmarks, latency numbers, and architecture whitepapers.
  3. *Step 3 (Polite Breakup):* Graceful closure with perpetual opt-out mechanism.

### 2.2 Live AI Reply Triage & Intent Classifier
Every incoming email reply is analyzed and routed automatically into 4 actionable categories:
1. **`interested`:** Detects demo requests, scheduling inquiries, and pricing interest. Recommends an instant calendar booking response (`https://cal.com/alex-sdr/15min`).
2. **`more_info`:** Detects technical inquiries, architecture questions, and benchmark requests. Generates grounded technical responses.
3. **`out_of_office`:** Identifies vacations, conferences (e.g. AWS re:Invent), and temporary leaves. Automatically snoozes the cadence until the prospect returns.
4. **`unsubscribe`:** Recognizes opt-out phrases (*"remove me"*, *"stop emailing"*, *"not interested"*). Immediately triggers the suppression engine.

### 2.3 Strict Deliverability & CAN-SPAM Compliance Gate
- **100% CAN-SPAM Adherence:** Every outbound email includes mandatory physical postal address verification (`SHIVAM ITCS Plaza, Suite 400`) and one-click unsubscribe token.
- **Automated Suppression Blacklist:** Unsubscribes are committed to an immutable blacklist; outbox dispatch hard-fails if an email matches a suppressed recipient.
- **Deliverability Health Meter:** Real-time monitoring of SPF (`v=spf1 include:_spf.mailgun.org`), DKIM (2048-bit RSA keys), and DMARC (`p=reject 100%`) records.
- **Domain Throttling:** Enforces safe warm-up curves (default 50 emails/day per domain) to preserve pristine IP and domain sender reputation.

### 2.4 5-Pool Dynamic AI Model Budget Router
- **Tiered Model Routing:** Routes lightweight reply classification to ultra-fast models (`groq/llama-3.3-70b-versatile` or `local/qwen2.5`) and complex copy generation to balanced models (`openai/gpt-4o-mini`).
- **Spend Ledgers & Circuit Breakers:** Per-tenant monthly spend caps with automatic fallback to offline local models when quotas are exceeded.
