from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_api_key_tenant
from app.db.session import get_db
from app.schemas.leads import PublicLeadCreate, PublicLeadResponse
from app.services import leads as lead_service
from app.services.n8n_dispatch import schedule_n8n_event
from app.services.qualification import maybe_auto_qualify
from app.services.rate_limit import enforce_public_rate_limit

settings = get_settings()

router = APIRouter(prefix="/v1/public", tags=["public"])


@router.post("/leads", response_model=PublicLeadResponse)
def submit_lead(
    payload: PublicLeadCreate,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    auth: Annotated[tuple, Depends(get_api_key_tenant)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PublicLeadResponse:
    api_key, tenant_id = auth
    enforce_public_rate_limit(tenant_id=str(tenant_id), api_key_id=str(api_key.id))

    try:
        lead, duplicate = lead_service.ingest_public_lead(
            db,
            tenant_id,
            payload,
            idempotency_key=idempotency_key,
        )
        qualification = maybe_auto_qualify(db, lead) if not duplicate else None
        db.commit()
        if not duplicate:
            schedule_n8n_event(
                background_tasks,
                event_type="lead.created",
                tenant_id=tenant_id,
                lead_id=lead.id,
                payload={"source": lead.source, "duplicate": False},
                idempotency_key=idempotency_key or f"lead.created:{lead.id}",
            )
            if qualification is not None:
                schedule_n8n_event(
                    background_tasks,
                    event_type="qualification.completed",
                    tenant_id=tenant_id,
                    lead_id=lead.id,
                    payload={
                        "priority": qualification.priority.value,
                        "intent_score": qualification.intent_score,
                    },
                    idempotency_key=f"qualification.completed:{qualification.id}",
                )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    message = "Lead already exists" if duplicate else "Lead accepted"
    return PublicLeadResponse(id=lead.id, duplicate=duplicate, message=message)