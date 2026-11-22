from services.compliance.can_spam import CANSPAMComplianceValidator

def test_can_spam_valid_footer():
    body = """Hi Sarah,

Saw your infrastructure growth. We'd love to connect.

Best,
Alex

---
100 Enterprise Way, Suite 400, San Francisco, CA 94105
Unsubscribe: https://outbound.acme.com/unsub"""

    val = CANSPAMComplianceValidator.validate_message(body)
    assert val["compliant"] is True
    assert val["has_unsubscribe_link"] is True
    assert val["has_physical_address"] is True
    assert val["status"] == "APPROVED_FOR_SEND"

def test_can_spam_missing_footer_rejected():
    raw_body = "Hey buy my product right now!"
    val = CANSPAMComplianceValidator.validate_message(raw_body)
    assert val["compliant"] is False
    assert val["status"] == "REJECTED_MISSING_FOOTER"
