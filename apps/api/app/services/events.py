from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.enums import ActorType
from app.models.lead import LeadEvent


def record_lead_event(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    lead_id: uuid.UUID | None,
    event_type: str,
    payload: dict | None = None,
    actor_type: ActorType = ActorType.system,
    actor_id: str | None = None,
    idempotency_key: str | None = None,
) -> LeadEvent:
    event = LeadEvent(
        tenant_id=tenant_id,
        lead_id=lead_id,
        event_type=event_type,
        payload=payload or {},
        actor_type=actor_type,
        actor_id=actor_id,
        idempotency_key=idempotency_key,
    )
    db.add(event)
    return event