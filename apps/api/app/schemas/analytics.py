from datetime import datetime

from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    total_leads: int
    new_today: int
    hot: int
    warm: int
    cold: int
    follow_up_pending: int
    conversion_rate: float


class ActivityItem(BaseModel):
    id: int
    event_type: str
    lead_id: str | None
    created_at: datetime
    payload: dict


class SourceBreakdownItem(BaseModel):
    source: str
    count: int