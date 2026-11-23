from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import LeadPriority, LeadStatus


class LeadCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=32)
    enquiry_text: str = Field(..., min_length=1, max_length=8000)
    source: str = Field(default="manual", max_length=64)
    source_detail: dict = Field(default_factory=dict)
    consent_marketing: bool = False
    consent_channel_email: bool = False
    consent_channel_whatsapp: bool = False
    metadata: dict = Field(default_factory=dict)


class PublicLeadCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=32)
    enquiry_text: str = Field(..., min_length=1, max_length=8000)
    source: str = Field(default="website", max_length=64)
    source_detail: dict = Field(default_factory=dict)
    consent_marketing: bool = False
    consent_channel_email: bool = False
    consent_channel_whatsapp: bool = False
    metadata: dict = Field(default_factory=dict)


class LeadUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=32)
    status: LeadStatus | None = None
    priority: LeadPriority | None = None
    assigned_user_id: UUID | None = None
    follow_up_paused: bool | None = None
    next_follow_up_at: datetime | None = None


class LeadNoteCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=5000)


class LeadNoteResponse(BaseModel):
    id: UUID
    body: str
    created_at: datetime
    user_id: UUID | None

    model_config = {"from_attributes": True}


class LeadResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    source: str
    source_detail: dict
    full_name: str
    email: str | None
    phone: str | None
    enquiry_text: str
    status: LeadStatus
    priority: LeadPriority
    assigned_user_id: UUID | None
    consent_marketing: bool
    consent_channel_email: bool
    consent_channel_whatsapp: bool
    last_interaction_at: datetime | None
    next_follow_up_at: datetime | None
    follow_up_paused: bool
    metadata: dict = Field(validation_alias="lead_metadata")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class PublicLeadResponse(BaseModel):
    id: UUID
    duplicate: bool = False
    message: str = "Lead accepted"


class LeadListResponse(BaseModel):
    items: list[LeadResponse]
    total: int
    page: int
    page_size: int