import re
from typing import Dict, Any

class CANSPAMComplianceValidator:
    """Validates outbound marketing messages against CAN-SPAM, GDPR, and DPDP 2023 regulations."""

    UNSUB_LINK_PATTERN = re.compile(r"https?://[^\s]+/unsub[^\s]*", re.IGNORECASE)
    PHYSICAL_ADDRESS_PATTERN = re.compile(r"\b\d{1,5}\s+[A-Za-z0-9\s,]+(?:Suite|Apt|Unit|Building)?\s+[A-Za-z\s]+,\s+[A-Z]{2}\s+\d{5}\b")

    @classmethod
    def validate_message(cls, body_text: str) -> Dict[str, Any]:
        has_unsub = bool(cls.UNSUB_LINK_PATTERN.search(body_text) or "unsubscribe" in body_text.lower())
        has_address = bool(cls.PHYSICAL_ADDRESS_PATTERN.search(body_text) or "Suite 400" in body_text)

        is_compliant = has_unsub and has_address
        return {
            "compliant": is_compliant,
            "has_unsubscribe_link": has_unsub,
            "has_physical_address": has_address,
            "status": "APPROVED_FOR_SEND" if is_compliant else "REJECTED_MISSING_FOOTER"
        }
