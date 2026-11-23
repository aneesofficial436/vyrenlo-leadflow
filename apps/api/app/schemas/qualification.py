from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import LeadPriority
from app.schemas.leads import LeadResponse


class QualificationLLMOutput(BaseModel):
    summary: str = Field(..., max_length=2000)
    category: str = Field(..., max_length=64)
    priority: Literal["hot", "warm", "cold"]
    intent_score: int = Field(..., ge=0, le=100)
    requirements: dict[str, Any] = Field(default_factory=dict)
    recommended_action: str = Field(..., max_length=500)
    confidence: float = Field(..., ge=0.0, le=1.0)


class QualificationResponse(BaseModel):
    id: UUID
    lead_id: UUID
    model: str
    prompt_version: str
    summary: str
    category: str
    intent_score: int
    priority: LeadPriority
    requirements: dict[str, Any]
    recommended_action: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LeadDetailResponse(BaseModel):
    lead: LeadResponse
    latest_qualification: QualificationResponse | None = None