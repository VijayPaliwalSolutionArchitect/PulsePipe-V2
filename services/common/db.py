from __future__ import annotations
import json
import logging
import sqlite3
from typing import Any, Dict, List, Optional

_logger = logging.getLogger("pulsepipe.db")


class PulsePipeStore:
    def __init__(self, db_path: str = "pulsepipe.db"):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()
        self._seed_data()

    def _init_schema(self):
        cur = self._conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            display_name TEXT NOT NULL,
            brand_color TEXT DEFAULT '#0284c7',
            monthly_budget_usd REAL DEFAULT 200.0,
            hard_cap_usd REAL DEFAULT 250.0,
            current_spend_usd REAL DEFAULT 0.0,
            sending_domain TEXT DEFAULT 'sales.acme.com',
            plan_tier TEXT DEFAULT 'enterprise',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS campaigns (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            title TEXT NOT NULL,
            target_segment TEXT NOT NULL,
            sdr_persona TEXT DEFAULT 'consultative',
            model_pool TEXT DEFAULT 'balanced',
            daily_send_limit INTEGER DEFAULT 50,
            status TEXT DEFAULT 'active',
            sent_count INTEGER DEFAULT 0,
            replied_count INTEGER DEFAULT 0,
            bounced_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES tenants (id)
        );

        CREATE TABLE IF NOT EXISTS prospects (
            id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL,
            company_name TEXT NOT NULL,
            title TEXT NOT NULL,
            linkedin_url TEXT,
            industry TEXT,
            tech_stack TEXT DEFAULT '[]',
            recent_signal TEXT,
            status TEXT DEFAULT 'sent',
            reply_intent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id),
            FOREIGN KEY (tenant_id) REFERENCES tenants (id)
        );

        CREATE TABLE IF NOT EXISTS sequences (
            id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL,
            step_number INTEGER NOT NULL,
            step_type TEXT DEFAULT 'email',
            delay_days INTEGER DEFAULT 2,
            subject_template TEXT NOT NULL,
            body_template TEXT NOT NULL,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
        );

        CREATE TABLE IF NOT EXISTS outbox_messages (
            id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL,
            prospect_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            recipient_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            body_text TEXT NOT NULL,
            step_number INTEGER DEFAULT 1,
            status TEXT DEFAULT 'delivered',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES campaigns (id),
            FOREIGN KEY (prospect_id) REFERENCES prospects (id)
        );

        CREATE TABLE IF NOT EXISTS replies (
            id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL,
            prospect_id TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            sender_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            body_text TEXT NOT NULL,
            reply_intent TEXT NOT NULL,
            confidence REAL DEFAULT 0.95,
            suggested_action TEXT,
            suggested_reply TEXT,
            status TEXT DEFAULT 'pending_review',
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS suppressions (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            email TEXT NOT NULL,
            reason TEXT DEFAULT 'unsubscribe',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sdr_personas (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            tone TEXT NOT NULL,
            system_prompt TEXT NOT NULL,
            is_default INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS query_audit_logs (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            campaign_id TEXT,
            action TEXT NOT NULL,
            model_used TEXT NOT NULL,
            tokens_used INTEGER DEFAULT 0,
            cost_usd REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        self._conn.commit()

    def _seed_data(self):
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) FROM tenants")
        if cur.fetchone()[0] == 0:
            cur.executemany("""
            INSERT INTO tenants (id, name, display_name, brand_color, monthly_budget_usd, hard_cap_usd, sending_domain)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                ("acme-sales", "Acme Enterprise Sales", "Acme AI SDR Outbound Hub", "#0284c7", 200.0, 250.0, "outbound.acme.com"),
                ("saas-growth", "SaaS Growth Accelerator", "Growth AI Engine", "#10b981", 150.0, 200.0, "mail.saasgrowth.io")
            ])

            cur.executemany("""
            INSERT INTO campaigns (id, tenant_id, title, target_segment, sdr_persona, status, sent_count, replied_count, bounced_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                ("camp-01", "acme-sales", "Q4 FinTech CTO Outbound Sprint", "FinTech Scaleups ($50M+ ARR)", "consultative", "active", 42, 6, 1),
                ("camp-02", "acme-sales", "Enterprise MLOps Leaders Outreach", "AI Infrastructure Companies", "challenger", "active", 28, 4, 0),
                ("camp-03", "saas-growth", "Series A B2B Founders Sequence", "Early Stage B2B SaaS", "founder-led", "active", 15, 2, 0)
            ])

            # Seed prospects
            prospects_seed = [
                ("pros-01", "camp-01", "acme-sales", "Sarah", "Chen", "sarah.chen@stripe.com", "Stripe Capital", "VP Engineering", "https://linkedin.com/in/sarahchen-tech", "FinTech", json.dumps(["Go", "Kubernetes", "AWS"]), "Expanding EMEA distributed engineering hub", "replied", "interested"),
                ("pros-02", "camp-01", "acme-sales", "David", "Miller", "david.m@plaid.com", "Plaid Technologies", "Head of Platform Architecture", "https://linkedin.com/in/davidmiller-plaid", "FinTech", json.dumps(["Rust", "AWS", "gRPC"]), "Upgrading core ingestion to Rust microservices", "replied", "more_info"),
                ("pros-03", "camp-01", "acme-sales", "Marcus", "Vance", "marcus@wandb.ai", "Weights & Biases", "VP MLOps Platform", "https://linkedin.com/in/marcusvance", "AI Tools", json.dumps(["Python", "PyTorch", "Kubernetes"]), "Launched automated LLM benchmark suite", "replied", "out_of_office"),
                ("pros-04", "camp-01", "acme-sales", "Elena", "Rostova", "elena@brex.com", "Brex Cards", "Director of Core Systems", "https://linkedin.com/in/elenarostova", "FinTech", json.dumps(["Elixir", "Kubernetes", "AWS"]), "Consolidating travel reconciliation workflows", "sent", None),
                ("pros-05", "camp-01", "acme-sales", "Kevin", "Bates", "kevin@unsub.example", "Legacy Finance Corp", "IT Manager", None, "Banking", json.dumps(["Java"]), None, "replied", "unsubscribe")
            ]
            cur.executemany("""
            INSERT INTO prospects (id, campaign_id, tenant_id, first_name, last_name, email, company_name, title, linkedin_url, industry, tech_stack, recent_signal, status, reply_intent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, prospects_seed)

            # Seed sequences
            cur.executemany("""
            INSERT INTO sequences (id, campaign_id, step_number, step_type, delay_days, subject_template, body_template)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                ("seq-01", "camp-01", 1, "email", 0, "Scaling distributed architecture at {{company_name}}", "Hi {{first_name}},\n\nSaw your team is expanding distributed engineering. We help scale Kubernetes pipelines.\n\nBest,\nAlex"),
                ("seq-02", "camp-01", 2, "follow_up", 3, "Quick follow up re: {{company_name}} infrastructure", "Hi {{first_name}},\n\nCircling back on my note re: cloud reliability.\n\nBest,\nAlex"),
                ("seq-03", "camp-01", 3, "breakup", 5, "Closing the loop for now", "Hi {{first_name}},\n\nAssuming you are focused on other priorities right now. Leaving you with our tech teardown.\n\nBest,\nAlex")
            ])

            # Seed replies
            replies_seed = [
                ("rep-01", "camp-01", "pros-01", "acme-sales", "sarah.chen@stripe.com", "Re: Scaling distributed architecture at Stripe Capital",
                 "Hi Alex, this aligns with our current Q4 roadmap. Can you send over your technical deck and calendar link for a 15-min call next Tuesday?",
                 "interested", 0.98, "Book demo meeting", "Hi Sarah, delighted to connect! Here is my direct scheduling link: https://cal.com/alex-sdr/15min", "pending_review"),
                
                ("rep-02", "camp-01", "pros-02", "acme-sales", "david.m@plaid.com", "Re: Scaling distributed architecture at Plaid Technologies",
                 "Thanks for reaching out. What are your benchmark latency numbers on gRPC streaming and AWS multi-region failover?",
                 "more_info", 0.94, "Send latency technical benchmarks", "Hi David, our verified p99 latency across multi-region AWS is 14.2ms. Attached is our technical whitepaper.", "pending_review"),

                ("rep-03", "camp-01", "pros-03", "acme-sales", "marcus@wandb.ai", "Automatic reply: Out of office",
                 "I am currently traveling for AWS re:Invent and will have limited email access until Dec 1st. For urgent matters contact team@wandb.ai.",
                 "out_of_office", 0.99, "Snooze sequence until Dec 2nd", "Automatic follow-up scheduled for Dec 2, 2026.", "processed"),

                ("rep-04", "camp-01", "pros-05", "acme-sales", "kevin@unsub.example", "Re: Scaling distributed architecture",
                 "Please remove me from your mailing list immediately. Do not contact again.",
                 "unsubscribe", 0.99, "Auto-suppressed (CAN-SPAM compliant)", "Unsubscribe confirmed; email added to suppression blacklist.", "processed")
            ]
            cur.executemany("""
            INSERT INTO replies (id, campaign_id, prospect_id, tenant_id, sender_email, subject, body_text, reply_intent, confidence, suggested_action, suggested_reply, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, replies_seed)

            # Seed suppressions
            cur.execute("""
            INSERT INTO suppressions (id, tenant_id, email, reason)
            VALUES ('sup-01', 'acme-sales', 'kevin@unsub.example', 'User opt-out / CAN-SPAM request')
            """)

            # Seed SDR personas
            cur.executemany("""
            INSERT INTO sdr_personas (id, tenant_id, name, tone, system_prompt, is_default)
            VALUES (?, ?, ?, ?, ?, ?)
            """, [
                ("pers-01", "acme-sales", "consultative", "Curious, peer-to-peer, technical", "You are an enterprise technical SDR. Write concise, highly personalized 3-sentence outbound emails highlighting prospect engineering signals.", 1),
                ("pers-02", "acme-sales", "challenger", "Direct, bold, metrics-focused", "You are a Challenger SDR. Challenge existing infrastructure costs and present proven ROI benchmarks.", 0),
                ("pers-03", "acme-sales", "founder-led", "Humble, vision-aligned, problem-solver", "You are the Founder reaching out directly. Speak founder-to-founder about technical bottlenecks.", 0)
            ])

            self._conn.commit()

    def get_tenants(self) -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM tenants")
        return [dict(r) for r in cur.fetchall()]

    def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def update_tenant_spend(self, tenant_id: str, cost_usd: float):
        cur = self._conn.cursor()
        cur.execute("UPDATE tenants SET current_spend_usd = current_spend_usd + ? WHERE id = ?", (cost_usd, tenant_id))
        self._conn.commit()

    def get_campaigns(self, tenant_id: str = "acme-sales") -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM campaigns WHERE tenant_id = ? ORDER BY created_at DESC", (tenant_id,))
        return [dict(r) for r in cur.fetchall()]

    def add_campaign(self, c: Dict[str, Any]):
        cur = self._conn.cursor()
        cur.execute("""
        INSERT INTO campaigns (id, tenant_id, title, target_segment, sdr_persona, model_pool, daily_send_limit, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (c["id"], c["tenant_id"], c["title"], c["target_segment"], c.get("sdr_persona", "consultative"), c.get("model_pool", "balanced"), c.get("daily_send_limit", 50), "active"))
        self._conn.commit()

    def get_prospects(self, campaign_id: Optional[str] = None, tenant_id: str = "acme-sales") -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        if campaign_id:
            cur.execute("SELECT * FROM prospects WHERE campaign_id = ? AND tenant_id = ? ORDER BY created_at DESC", (campaign_id, tenant_id))
        else:
            cur.execute("SELECT * FROM prospects WHERE tenant_id = ? ORDER BY created_at DESC", (tenant_id,))
        rows = [dict(r) for r in cur.fetchall()]
        for r in rows:
            r["tech_stack"] = json.loads(r["tech_stack"]) if isinstance(r["tech_stack"], str) else r["tech_stack"]
        return rows

    def get_sequences(self, campaign_id: str) -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM sequences WHERE campaign_id = ? ORDER BY step_number ASC", (campaign_id,))
        return [dict(r) for r in cur.fetchall()]

    def get_replies(self, tenant_id: str = "acme-sales") -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM replies WHERE tenant_id = ? ORDER BY received_at DESC", (tenant_id,))
        return [dict(r) for r in cur.fetchall()]

    def get_suppressions(self, tenant_id: str = "acme-sales") -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM suppressions WHERE tenant_id = ? ORDER BY created_at DESC", (tenant_id,))
        return [dict(r) for r in cur.fetchall()]

    def is_suppressed(self, tenant_id: str, email: str) -> bool:
        cur = self._conn.cursor()
        cur.execute("SELECT 1 FROM suppressions WHERE tenant_id = ? AND email = ?", (tenant_id, email.lower().strip()))
        return cur.fetchone() is not None

    def add_suppression(self, tenant_id: str, email: str, reason: str = "unsubscribe"):
        cur = self._conn.cursor()
        cur.execute("""
        INSERT OR REPLACE INTO suppressions (id, tenant_id, email, reason)
        VALUES (?, ?, ?, ?)
        """, (f"sup-{abs(hash(email))%1000000}", tenant_id, email.lower().strip(), reason))
        self._conn.commit()

    def get_personas(self, tenant_id: str = "acme-sales") -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM sdr_personas WHERE tenant_id = ?", (tenant_id,))
        return [dict(r) for r in cur.fetchall()]

    def update_persona(self, persona_id: str, prompt: str, tone: str):
        cur = self._conn.cursor()
        cur.execute("UPDATE sdr_personas SET system_prompt = ?, tone = ? WHERE id = ?", (prompt, tone, persona_id))
        self._conn.commit()

    def log_query_audit(self, log_data: Dict[str, Any]):
        cur = self._conn.cursor()
        cur.execute("""
        INSERT INTO query_audit_logs (id, tenant_id, campaign_id, action, model_used, tokens_used, cost_usd)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            log_data["id"], log_data["tenant_id"], log_data.get("campaign_id"),
            log_data["action"], log_data["model_used"], log_data.get("tokens_used", 0),
            log_data.get("cost_usd", 0.0)
        ))
        self._conn.commit()

    def get_audit_logs(self, tenant_id: str = "acme-sales") -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM query_audit_logs WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 50", (tenant_id,))
        return [dict(r) for r in cur.fetchall()]


db = PulsePipeStore()
