from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.analytics import ActivityItem, AnalyticsOverview, SourceBreakdownItem
from app.services import analytics as analytics_service

router = APIRouter(prefix="/v1/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def overview(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
) -> AnalyticsOverview:
    data = analytics_service.get_overview(db, current.tenant_id)
    return AnalyticsOverview(**data)


@router.get("/sources", response_model=list[SourceBreakdownItem])
def sources(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
) -> list[SourceBreakdownItem]:
    rows = analytics_service.get_source_breakdown(db, current.tenant_id)
    return [SourceBreakdownItem(**r) for r in rows]


@router.get("/activity", response_model=list[ActivityItem])
def activity(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
    limit: int = Query(12, ge=1, le=50),
) -> list[ActivityItem]:
    events = analytics_service.get_recent_activity(db, current.tenant_id, limit=limit)
    return [
        ActivityItem(
            id=e.id,
            event_type=e.event_type,
            lead_id=str(e.lead_id) if e.lead_id else None,
            created_at=e.created_at,
            payload=e.payload,
        )
        for e in events
    ]