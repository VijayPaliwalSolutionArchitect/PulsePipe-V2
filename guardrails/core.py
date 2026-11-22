import re
from typing import Dict, Any

class DPDPGuardrails:
    """Enterprise DPDP 2023 & GDPR compliant PII Redactor, Prompt Injection, and Outbound Authorizer."""

    PAN_PATTERN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b")
    AADHAAR_PATTERN = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
    SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

    INJECTION_TRIGGERS = [
        "ignore previous instructions",
        "system prompt override",
        "drop table",
        "reveal api keys",
        "send spam to all"
    ]

    @classmethod
    def redact_pii(cls, text: str) -> str:
        s = cls.PAN_PATTERN.sub("[REDACTED_PAN]", text)
        s = cls.AADHAAR_PATTERN.sub("[REDACTED_AADHAAR]", s)
        s = cls.SSN_PATTERN.sub("[REDACTED_SSN]", s)
        return s

    @classmethod
    def check_prompt_injection(cls, query: str) -> bool:
        q_lower = query.lower()
        return any(t in q_lower for t in cls.INJECTION_TRIGGERS)

    @classmethod
    def authorize_outbound_send(cls, role: str, volume: int) -> bool:
        if volume > 1000 and role != "admin":
            return False
        return True
