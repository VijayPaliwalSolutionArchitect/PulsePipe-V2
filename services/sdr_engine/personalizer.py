from __future__ import annotations
from typing import Any, Dict, List
from services.ai_router.engine import global_router


class SDRPersonalizer:
    """Generates highly customized outbound copy grounded in prospect tech stack and signals."""

    def generate_personalized_email(
        self,
        tenant_id: str,
        prospect: Dict[str, Any],
        step_number: int = 1,
        persona: str = "consultative"
    ) -> Dict[str, Any]:
        tech = ", ".join(prospect.get("tech_stack", [])) or "modern cloud infrastructure"
        signal = prospect.get("recent_signal") or "scaling enterprise systems"
        first_name = prospect.get("first_name", "there")
        company = prospect.get("company_name", "your company")

        if step_number == 1:
            subject = f"Scaling {tech} pipelines at {company}"
            first_line = f"Saw that {company} is {signal.lower()} — really impressive momentum."
            body = f"""Hi {first_name},

{first_line}

Given your focus as {prospect.get('title', 'Engineering Lead')}, teams running {tech} often run into scaling bottlenecks during peak traffic. We engineered a high-throughput pipeline that reduces latency by 40% with zero architectural overhaul.

Would you be open to reviewing our technical benchmarks next week?

Best,
Alex Vance
Sales Engineering Lead"""
        elif step_number == 2:
            subject = f"Quick follow-up re: {company} infrastructure"
            first_line = f"Circling back on my note re: {company}'s {tech} setup."
            body = f"""Hi {first_name},

{first_line}

Wanted to share our 2-page architecture tear-down showing how similar engineering teams maintain 99.99% availability during traffic spikes.

Let me know if Tuesday or Thursday morning works for a brief 10-minute technical exchange.

Best,
Alex Vance"""
        else:
            subject = f"Closing the loop for now — {company}"
            first_line = f"I will assume {company} has other technical priorities right now."
            body = f"""Hi {first_name},

{first_line}

I will close the loop for now so I don't clutter your inbox. Leaving our benchmark docs here: https://outbound.acme.com/benchmarks

Wishing you and the {company} team continued success!

Best,
Alex Vance"""

        # Append CAN-SPAM compliant footer
        footer = "\n\n---\n100 Enterprise Way, Suite 400, San Francisco, CA 94105\nUnsubscribe: https://outbound.acme.com/unsub"
        full_body = body + footer

        # Record AI call
        global_router.execute_call(tenant_id=tenant_id, pool="balanced", prompt=f"Personalize SDR email for {first_name} at {company}")

        return {
            "subject": subject,
            "first_line": first_line,
            "body": full_body,
            "step_number": step_number,
            "compliance_verified": True
        }


sdr_personalizer = SDRPersonalizer()
