from __future__ import annotations

import hashlib
import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import ActorType, LeadPriority, LeadStatus
from app.models.lead import IngestionIdempotency, Lead, LeadNote
from app.schemas.leads import LeadCreate, LeadUpdate, PublicLeadCreate
from app.services.events import record_lead_event

def normalize_email(email: str | None) -> str | None:
    if not email:
        return None
    return email.strip().lower()


def normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    return digits if digits else None


def compute_dedup_key(tenant_id: uuid.UUID, email: str | None, phone: str | None) -> str:
    norm_email = normalize_email(email)
    norm_phone = normalize_phone(phone)
    if not norm_email and not norm_phone:
        raw = f"{tenant_id}:anonymous:{uuid.uuid4()}"
    elif norm_email:
        raw = f"{tenant_id}:email:{norm_email}"
    else:
        raw = f"{tenant_id}:phone:{norm_phone}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _lead_from_payload(
    tenant_id: uuid.UUID,
    payload: LeadCreate | PublicLeadCreate,
    *,
    source_override: str | None = None,
) -> Lead:
    source = source_override or payload.source
    return Lead(
        tenant_id=tenant_id,
        source=source,
        source_detail=payload.source_detail,
        full_name=payload.full_name.strip(),
        email=normalize_email(str(payload.email)) if payload.email else None,
        phone=normalize_phone(payload.phone),
        enquiry_text=payload.enquiry_text.strip(),
        status=LeadStatus.new,
        priority=LeadPriority.unqualified,
        consent_marketing=payload.consent_marketing,
        consent_channel_email=payload.consent_channel_email,
        consent_channel_whatsapp=payload.consent_channel_whatsapp,
        dedup_key=compute_dedup_key(
            tenant_id,
            str(payload.email) if payload.email else None,
            payload.phone,
        ),
        lead_metadata=payload.metadata,
        last_interaction_at=datetime.now(UTC),
    )


def create_lead_manual(db: Session, tenant_id: uuid.UUID, payload: LeadCreate, actor_id: str) -> Lead:
    lead = _lead_from_payload(tenant_id, payload)
    db.add(lead)
    db.flush()
    record_lead_event(
        db,
        tenant_id=tenant_id,
        lead_id=lead.id,
        event_type="lead.created",
        payload={"source": lead.source},
        actor_type=ActorType.user,
        actor_id=actor_id,
    )
    return lead


def ingest_public_lead(
    db: Session,
    tenant_id: uuid.UUID,
    payload: PublicLeadCreate,
    *,
    idempotency_key: str | None,
) -> tuple[Lead, bool]:
    if idempotency_key:
        existing = db.scalar(
            select(IngestionIdempotency).where(
                IngestionIdempotency.tenant_id == tenant_id,
                IngestionIdempotency.idempotency_key == idempotency_key,
            )
        )
        if existing:
            lead = db.get(Lead, existing.lead_id)
            if lead:
                return lead, True

    if not payload.email and not payload.phone:
        raise ValueError("email_or_phone_required")

    dedup_key = compute_dedup_key(tenant_id, str(payload.email) if payload.email else None, payload.phone)
    existing_lead = db.scalar(select(Lead).where(Lead.tenant_id == tenant_id, Lead.dedup_key == dedup_key))
    if existing_lead is not None:
        record_lead_event(
            db,
            tenant_id=tenant_id,
            lead_id=existing_lead.id,
            event_type="lead.duplicate_ingest",
            payload={"source": payload.source},
            actor_type=ActorType.system,
        )
        return existing_lead, True

    lead = _lead_from_payload(tenant_id, payload)
    lead.dedup_key = dedup_key
    db.add(lead)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        existing_lead = db.scalar(select(Lead).where(Lead.tenant_id == tenant_id, Lead.dedup_key == dedup_key))
        if existing_lead is None:
            raise
        return existing_lead, True

    record_lead_event(
        db,
        tenant_id=tenant_id,
        lead_id=lead.id,
        event_type="lead.created",
        payload={"source": lead.source, "channel": "public_api"},
        actor_type=ActorType.system,
        idempotency_key=idempotency_key,
    )

    if idempotency_key:
        db.add(
            IngestionIdempotency(
                tenant_id=tenant_id,
                idempotency_key=idempotency_key,
                lead_id=lead.id,
            )
        )

    return lead, False


def list_leads(
    db: Session,
    tenant_id: uuid.UUID,
    *,
    page: int,
    page_size: int,
    status: LeadStatus | None,
    priority: LeadPriority | None,
    search: str | None,
    sort: str,
) -> tuple[list[Lead], int]:
    filters = [Lead.tenant_id == tenant_id, Lead.deleted_at.is_(None)]
    if status:
        filters.append(Lead.status == status)
    if priority:
        filters.append(Lead.priority == priority)
    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                Lead.full_name.ilike(term),
                Lead.email.ilike(term),
                Lead.phone.ilike(term),
                Lead.enquiry_text.ilike(term),
            )
        )

    query = select(Lead).where(*filters)
    total = db.scalar(select(func.count(Lead.id)).where(*filters)) or 0

    if sort == "created_at_asc":
        query = query.order_by(Lead.created_at.asc())
    elif sort == "priority_desc":
        query = query.order_by(Lead.priority.desc(), Lead.created_at.desc())
    else:
        query = query.order_by(Lead.created_at.desc())

    offset = (page - 1) * page_size
    leads = list(db.scalars(query.offset(offset).limit(page_size)).all())
    return leads, total


def get_lead(db: Session, tenant_id: uuid.UUID, lead_id: uuid.UUID) -> Lead | None:
    return db.scalar(
        select(Lead).where(Lead.id == lead_id, Lead.tenant_id == tenant_id, Lead.deleted_at.is_(None))
    )


def update_lead(db: Session, lead: Lead, payload: LeadUpdate, actor_id: str) -> Lead:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key == "email" and value is not None:
            value = normalize_email(str(value))
        if key == "phone":
            value = normalize_phone(value)
        setattr(lead, key, value)
    lead.updated_at = datetime.now(UTC)
    record_lead_event(
        db,
        tenant_id=lead.tenant_id,
        lead_id=lead.id,
        event_type="lead.updated",
        payload={"fields": list(data.keys())},
        actor_type=ActorType.user,
        actor_id=actor_id,
    )
    return lead


def add_lead_note(db: Session, lead: Lead, body: str, user_id: uuid.UUID) -> LeadNote:
    note = LeadNote(tenant_id=lead.tenant_id, lead_id=lead.id, user_id=user_id, body=body.strip())
    db.add(note)
    record_lead_event(
        db,
        tenant_id=lead.tenant_id,
        lead_id=lead.id,
        event_type="lead.note_added",
        payload={},
        actor_type=ActorType.user,
        actor_id=str(user_id),
    )
    return note

