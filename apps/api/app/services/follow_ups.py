from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import FollowUpStatus, LeadStatus
from app.models.lead import AutomationSettings, FollowUp, Lead
from app.models.lead import LeadQualification
from app.services.communications import (
    CommunicationError,
    can_email_lead,
    create_outbound_email,
    send_communication,
)
from app.services.events import record_lead_event
from app.services.message_generation import generate_follow_up_email
from app.models.enums import ActorType


def list_due_follow_ups(db: Session, tenant_id: uuid.UUID, *, limit: int = 50) -> list[Lead]:
    now = datetime.now(UTC)
    terminal = [LeadStatus.won, LeadStatus.lost, LeadStatus.spam, LeadStatus.opted_out]
    return list(
        db.scalars(
            select(Lead)
            .where(
                Lead.tenant_id == tenant_id,
                Lead.deleted_at.is_(None),
                Lead.follow_up_paused.is_(False),
                Lead.next_follow_up_at.isnot(None),
                Lead.next_follow_up_at <= now,
                Lead.status.notin_(terminal),
            )
            .order_by(Lead.next_follow_up_at.asc())
            .limit(limit)
        ).all()
    )


def _get_settings(db: Session, tenant_id: uuid.UUID) -> AutomationSettings:
    row = db.get(AutomationSettings, tenant_id)
    if row is None:
        row = AutomationSettings(tenant_id=tenant_id)
        db.add(row)
        db.flush()
    return row


def schedule_follow_up_sequence(db: Session, lead: Lead) -> None:
    if lead.follow_up_paused or not can_email_lead(lead):
        return

    settings = _get_settings(db, lead.tenant_id)
    intervals = settings.follow_up_intervals_hours or [24, 72, 168]
    max_steps = min(settings.max_follow_ups, len(intervals))

    existing = db.scalar(select(func.count(FollowUp.id)).where(FollowUp.lead_id == lead.id))
    if existing and existing > 0:
        return

    now = datetime.now(UTC)
    for step in range(1, max_steps + 1):
        scheduled = now + timedelta(hours=intervals[step - 1])
        db.add(
            FollowUp(
                tenant_id=lead.tenant_id,
                lead_id=lead.id,
                sequence_step=step,
                scheduled_at=scheduled,
                status=FollowUpStatus.scheduled,
            )
        )
    lead.next_follow_up_at = now + timedelta(hours=intervals[0])
    record_lead_event(
        db,
        tenant_id=lead.tenant_id,
        lead_id=lead.id,
        event_type="follow_up.scheduled",
        payload={"steps": max_steps},
        actor_type=ActorType.system,
    )


def _latest_qualification(db: Session, lead_id: uuid.UUID) -> LeadQualification | None:
    return db.scalar(
        select(LeadQualification)
        .where(LeadQualification.lead_id == lead_id)
        .order_by(LeadQualification.created_at.desc())
        .limit(1)
    )


def execute_next_follow_up(db: Session, lead: Lead, *, actor_id: str | None = "n8n") -> dict:
    if lead.follow_up_paused or not can_email_lead(lead):
        return {"skipped": True, "reason": "paused_or_no_consent"}

    follow = db.scalar(
        select(FollowUp)
        .where(
            FollowUp.lead_id == lead.id,
            FollowUp.status == FollowUpStatus.scheduled,
            FollowUp.scheduled_at <= datetime.now(UTC),
        )
        .order_by(FollowUp.sequence_step.asc())
        .limit(1)
    )
    if follow is None:
        lead.next_follow_up_at = None
        return {"skipped": True, "reason": "no_due_step"}

    qualification = _latest_qualification(db, lead.id)
    subject, body = generate_follow_up_email(lead=lead, step=follow.sequence_step, qualification=qualification)
    from app.models.enums import CommunicationStatus

    comm = create_outbound_email(db, lead=lead, subject=subject, body=body, ai_generated=True)

    if comm.status == CommunicationStatus.pending_approval:
        record_lead_event(
            db,
            tenant_id=lead.tenant_id,
            lead_id=lead.id,
            event_type="follow_up.pending_approval",
            payload={"step": follow.sequence_step, "communication_id": str(comm.id)},
            actor_type=ActorType.system,
        )
        return {
            "skipped": False,
            "pending_approval": True,
            "communication_id": str(comm.id),
            "step": follow.sequence_step,
        }

    try:
        send_communication(db, comm, actor_id=actor_id)
        follow.status = FollowUpStatus.sent
        follow.executed_at = datetime.now(UTC)
        follow.communication_id = comm.id
    except CommunicationError as exc:
        if str(exc) == "consent_or_email_missing":
            follow.status = FollowUpStatus.skipped
            follow.cancellation_reason = str(exc)
        else:
            follow.status = FollowUpStatus.failed
            follow.cancellation_reason = str(exc)
        record_lead_event(
            db,
            tenant_id=lead.tenant_id,
            lead_id=lead.id,
            event_type="follow_up.failed",
            payload={"step": follow.sequence_step, "error": str(exc)},
            actor_type=ActorType.system,
        )
        return {"skipped": False, "failed": True, "error": str(exc)}

    next_follow = db.scalar(
        select(FollowUp)
        .where(FollowUp.lead_id == lead.id, FollowUp.status == FollowUpStatus.scheduled)
        .order_by(FollowUp.sequence_step.asc())
        .limit(1)
    )
    lead.next_follow_up_at = next_follow.scheduled_at if next_follow else None

    record_lead_event(
        db,
        tenant_id=lead.tenant_id,
        lead_id=lead.id,
        event_type="follow_up.sent",
        payload={"step": follow.sequence_step, "communication_id": str(comm.id)},
        actor_type=ActorType.system,
    )
    return {
        "skipped": False,
        "step": follow.sequence_step,
        "communication_id": str(comm.id),
        "status": comm.status.value,
    }


def cancel_pending_follow_ups(db: Session, lead: Lead, reason: str) -> None:
    rows = db.scalars(select(FollowUp).where(FollowUp.lead_id == lead.id, FollowUp.status == FollowUpStatus.scheduled))
    for row in rows:
        row.status = FollowUpStatus.cancelled
        row.cancellation_reason = reason
    lead.next_follow_up_at = None