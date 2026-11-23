from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import LeadPriority, LeadStatus
from app.models.lead import Lead, LeadEvent


def get_overview(db: Session, tenant_id: uuid.UUID) -> dict:
    base = Lead.tenant_id == tenant_id
    not_deleted = Lead.deleted_at.is_(None)

    total_leads = db.scalar(select(func.count(Lead.id)).where(base, not_deleted)) or 0

    start_of_day = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    new_today = (
        db.scalar(
            select(func.count(Lead.id)).where(base, not_deleted, Lead.created_at >= start_of_day)
        )
        or 0
    )

    def count_priority(p: LeadPriority) -> int:
        return db.scalar(select(func.count(Lead.id)).where(base, not_deleted, Lead.priority == p)) or 0

    hot = count_priority(LeadPriority.hot)
    warm = count_priority(LeadPriority.warm)
    cold = count_priority(LeadPriority.cold)

    now = datetime.now(UTC)
    follow_up_pending = (
        db.scalar(
            select(func.count(Lead.id)).where(
                base,
                not_deleted,
                Lead.follow_up_paused.is_(False),
                Lead.next_follow_up_at.isnot(None),
                Lead.next_follow_up_at <= now + timedelta(days=7),
            )
        )
        or 0
    )

    won = (
        db.scalar(select(func.count(Lead.id)).where(base, not_deleted, Lead.status == LeadStatus.won))
        or 0
    )
    closed = (
        db.scalar(
            select(func.count(Lead.id)).where(
                base,
                not_deleted,
                Lead.status.in_([LeadStatus.won, LeadStatus.lost]),
            )
        )
        or 0
    )
    conversion_rate = round((won / closed) * 100, 1) if closed else 0.0

    return {
        "total_leads": total_leads,
        "new_today": new_today,
        "hot": hot,
        "warm": warm,
        "cold": cold,
        "follow_up_pending": follow_up_pending,
        "conversion_rate": conversion_rate,
    }


def get_source_breakdown(db: Session, tenant_id: uuid.UUID) -> list[dict]:
    rows = db.execute(
        select(Lead.source, func.count(Lead.id))
        .where(Lead.tenant_id == tenant_id, Lead.deleted_at.is_(None))
        .group_by(Lead.source)
        .order_by(func.count(Lead.id).desc())
    ).all()
    return [{"source": source, "count": count} for source, count in rows]


def get_recent_activity(db: Session, tenant_id: uuid.UUID, limit: int = 12) -> list[LeadEvent]:
    return list(
        db.scalars(
            select(LeadEvent)
            .where(LeadEvent.tenant_id == tenant_id)
            .order_by(LeadEvent.created_at.desc())
            .limit(limit)
        ).all()
    )