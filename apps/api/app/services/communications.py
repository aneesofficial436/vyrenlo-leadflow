from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import (
    ActorType,
    CommunicationChannel,
    CommunicationDirection,
    CommunicationStatus,
    LeadStatus,
)
from app.models.lead import Communication, Lead, TenantAiConfig
from app.services.email_delivery import EmailDeliveryError, send_email
from app.services.events import record_lead_event


class CommunicationError(Exception):
    pass


def can_email_lead(lead: Lead) -> bool:
    return bool(lead.email and lead.consent_channel_email)


def create_outbound_email(
    db: Session,
    *,
    lead: Lead,
    subject: str,
    body: str,
    ai_generated: bool = False,
    initial_status: CommunicationStatus | None = None,
) -> Communication:
    cfg = db.get(TenantAiConfig, lead.tenant_id)
    require_approval = cfg.require_approval_for_outbound if cfg else True
    status = initial_status or (
        CommunicationStatus.pending_approval if require_approval else CommunicationStatus.draft
    )

    row = Communication(
        tenant_id=lead.tenant_id,
        lead_id=lead.id,
        channel=CommunicationChannel.email,
        direction=CommunicationDirection.outbound,
        subject=subject,
        body=body,
        status=status,
        ai_generated=ai_generated,
    )
    db.add(row)
    return row


def send_communication(db: Session, comm: Communication, *, actor_id: str | None = None) -> Communication:
    if comm.channel != CommunicationChannel.email:
        raise CommunicationError("unsupported_channel")
    if comm.direction != CommunicationDirection.outbound:
        raise CommunicationError("invalid_direction")
    if comm.status not in (CommunicationStatus.draft, CommunicationStatus.pending_approval, CommunicationStatus.failed):
        raise CommunicationError("invalid_status")

    lead = db.get(Lead, comm.lead_id)
    if lead is None:
        raise CommunicationError("lead_not_found")
    if not can_email_lead(lead):
        comm.status = CommunicationStatus.failed
        comm.error = "consent_or_email_missing"
        raise CommunicationError("consent_or_email_missing")

    try:
        message_id = send_email(
            to_address=lead.email,  # type: ignore[arg-type]
            subject=comm.subject or "Message from Vyrenlo",
            body=comm.body,
        )
    except EmailDeliveryError as exc:
        comm.status = CommunicationStatus.failed
        comm.error = str(exc)
        raise CommunicationError(str(exc)) from exc

    now = datetime.now(UTC)
    comm.status = CommunicationStatus.sent
    comm.provider_message_id = message_id
    comm.sent_at = now
    comm.error = None
    lead.last_interaction_at = now
    if lead.status in (LeadStatus.new, LeadStatus.qualified):
        lead.status = LeadStatus.contacted

    record_lead_event(
        db,
        tenant_id=lead.tenant_id,
        lead_id=lead.id,
        event_type="communication.sent",
        payload={"channel": "email", "communication_id": str(comm.id)},
        actor_type=ActorType.user if actor_id else ActorType.system,
        actor_id=actor_id,
    )
    return comm


def approve_communication(db: Session, comm: Communication, user_id: uuid.UUID) -> Communication:
    if comm.status != CommunicationStatus.pending_approval:
        raise CommunicationError("not_pending_approval")
    comm.status = CommunicationStatus.draft
    comm.approved_by_user_id = user_id
    return comm


def record_inbound_email(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    from_email: str,
    subject: str | None,
    body: str,
) -> Communication | None:
    email = from_email.strip().lower()
    lead = db.scalar(select(Lead).where(Lead.tenant_id == tenant_id, Lead.email == email, Lead.deleted_at.is_(None)))
    if lead is None:
        return None

    comm = Communication(
        tenant_id=tenant_id,
        lead_id=lead.id,
        channel=CommunicationChannel.email,
        direction=CommunicationDirection.inbound,
        subject=subject,
        body=body,
        status=CommunicationStatus.received,
    )
    db.add(comm)

    now = datetime.now(UTC)
    lead.last_interaction_at = now
    lead.follow_up_paused = True
    lead.status = LeadStatus.engaged
    from app.services.follow_ups import cancel_pending_follow_ups

    cancel_pending_follow_ups(db, lead, "customer_responded")

    record_lead_event(
        db,
        tenant_id=tenant_id,
        lead_id=lead.id,
        event_type="communication.received",
        payload={"channel": "email"},
        actor_type=ActorType.lead,
        actor_id=email,
    )
    record_lead_event(
        db,
        tenant_id=tenant_id,
        lead_id=lead.id,
        event_type="follow_up.paused",
        payload={"reason": "customer_responded"},
        actor_type=ActorType.system,
    )
    return comm


def list_communications_for_lead(db: Session, tenant_id: uuid.UUID, lead_id: uuid.UUID) -> list[Communication]:
    return list(
        db.scalars(
            select(Communication)
            .where(Communication.tenant_id == tenant_id, Communication.lead_id == lead_id)
            .order_by(Communication.created_at.desc())
        ).all()
    )


def list_pending_approvals(db: Session, tenant_id: uuid.UUID, *, limit: int = 50) -> list[Communication]:
    return list(
        db.scalars(
            select(Communication)
            .where(
                Communication.tenant_id == tenant_id,
                Communication.status == CommunicationStatus.pending_approval,
            )
            .order_by(Communication.created_at.desc())
            .limit(limit)
        ).all()
    )