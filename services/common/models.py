from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

class ReplyIntent(str, Enum):
    INTERESTED = "interested"
    MORE_INFO = "more_info"
    OUT_OF_OFFICE = "out_of_office"
    UNSUBSCRIBE = "unsubscribe"
    BOUNCED = "bounced"
    NEUTRAL = "neutral"

class StepType(str, Enum):
    EMAIL = "email"
    FOLLOW_UP = "follow_up"
    LINKEDIN_TOUCH = "linkedin_touch"
    BREAKUP = "breakup"

class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

class SequenceStep(BaseModel):
    step_number: int
    step_type: StepType = StepType.EMAIL
    delay_days: int = 2
    subject_template: str
    body_template: str

class ProspectRecord(BaseModel):
    id: str
    campaign_id: str
    tenant_id: str
    first_name: str
    last_name: str
    email: str
    company_name: str
    title: str
    linkedin_url: Optional[str] = None
    industry: str
    tech_stack: List[str] = Field(default_factory=list)
    recent_signal: Optional[str] = None
    status: str = "queued"
    reply_intent: Optional[ReplyIntent] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class CampaignCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    title: str
    target_segment: str
    sdr_persona: str = "consultative"
    model_pool: str = "balanced"
    daily_send_limit: int = 50
    tenant_id: Optional[str] = "acme-sales"

class EmailOutboxMessage(BaseModel):
    id: str
    campaign_id: str
    prospect_id: str
    tenant_id: str
    recipient_email: str
    subject: str
    body_text: str
    step_number: int
    status: str = "sent"
    sent_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
