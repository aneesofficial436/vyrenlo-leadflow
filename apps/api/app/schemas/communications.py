from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import CommunicationDirection, CommunicationStatus


class CommunicationResponse(BaseModel):
    id: UUID
    lead_id: UUID
    channel: str
    direction: CommunicationDirection
    subject: str | None
    body: str
    status: CommunicationStatus
    ai_generated: bool
    sent_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InboundEmailPayload(BaseModel):
    tenant_id: UUID
    from_email: str = Field(..., min_length=3, max_length=255)
    subject: str | None = Field(None, max_length=512)
    body: str = Field(..., min_length=1, max_length=20000)


class FollowUpExecuteResponse(BaseModel):
    lead_id: UUID
    result: dict