from __future__ import annotations
from typing import Any, Dict
from services.common.db import db


class ReplyTriageClassifier:
    """Classifies inbound prospect email responses into actionable intent categories."""

    INTERESTED_TRIGGERS = ["calendar", "schedule", "demo", "call", "next week", "pricing", "send over deck", "discuss"]
    MORE_INFO_TRIGGERS = ["benchmarks", "whitepaper", "documentation", "how do you compare", "latency numbers", "more info"]
    OOTO_TRIGGERS = ["out of office", "out of the office", "automatic reply", "vacation", "limited access", "limited email access", "re:invent", "returning on", "automated response", "away from"]
    UNSUB_TRIGGERS = ["unsubscribe", "remove me", "not interested", "stop emailing", "do not contact", "spam", "take me off"]

    def classify_reply(self, subject: str, body: str) -> Dict[str, Any]:
        text = f"{subject} {body}".lower()

        # Priority 1: Unsubscribe & Opt-out (CAN-SPAM mandatory)
        if any(w in text for w in self.UNSUB_TRIGGERS):
            return {
                "intent": "unsubscribe",
                "confidence": 0.99,
                "suggested_action": "Auto-suppressed (CAN-SPAM compliant)",
                "suggested_reply": "Unsubscribe confirmed; email added to suppression blacklist."
            }

        # Priority 2: Out of Office
        if any(w in text for w in self.OOTO_TRIGGERS):
            return {
                "intent": "out_of_office",
                "confidence": 0.98,
                "suggested_action": "Snooze sequence for 7 days",
                "suggested_reply": "Sequence paused until prospect returns."
            }

        # Priority 3: Interested / Meeting Request
        if any(w in text for w in self.INTERESTED_TRIGGERS):
            return {
                "intent": "interested",
                "confidence": 0.96,
                "suggested_action": "Book demo meeting",
                "suggested_reply": "Delighted to connect! Here is my direct booking link: https://cal.com/alex-sdr/15min"
            }

        # Priority 4: Information Request
        if any(w in text for w in self.MORE_INFO_TRIGGERS):
            return {
                "intent": "more_info",
                "confidence": 0.92,
                "suggested_action": "Send technical architecture whitepaper",
                "suggested_reply": "Here are our verified performance benchmarks and technical whitepaper: https://outbound.acme.com/docs"
            }

        # Default: Neutral
        return {
            "intent": "neutral",
            "confidence": 0.85,
            "suggested_action": "Review manually",
            "suggested_reply": "Thank you for getting back to us. How can we best assist?"
        }


reply_classifier = ReplyTriageClassifier()
