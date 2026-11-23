from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class WorkflowRunCreate(BaseModel):
    tenant_id: UUID | None = None
    workflow_name: str = Field(..., min_length=1, max_length=128)
    n8n_execution_id: str | None = None
    status: str = Field(..., pattern="^(success|failed|running|retrying)$")
    error_message: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class WorkflowRunResponse(BaseModel):
    id: UUID
    workflow_name: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FollowUpDueItem(BaseModel):
    lead_id: UUID
    full_name: str
    email: str | None
    priority: str
    next_follow_up_at: datetime


class StaffNotifyResponse(BaseModel):
    ok: bool = True
    message: str = "Staff notification recorded"


class DailySummaryResponse(BaseModel):
    overview: dict[str, Any]
    message: str