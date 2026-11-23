from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.internal import verify_internal_service_token
from app.db.session import get_db
from app.models.enums import ActorType
from app.schemas.communications import FollowUpExecuteResponse, InboundEmailPayload
from app.schemas.internal import (
    DailySummaryResponse,
    FollowUpDueItem,
    StaffNotifyResponse,
    WorkflowRunCreate,
    WorkflowRunResponse,
)
from app.schemas.leads import LeadResponse
from app.schemas.qualification import QualificationResponse
from app.services import analytics as analytics_service
from app.services import communications as comm_service
from app.services import follow_ups as follow_up_service
from app.services import leads as lead_service
from app.services.email_delivery import EmailDeliveryError, send_email
from app.services.events import record_lead_event
from app.services.n8n_dispatch import schedule_n8n_event
from app.services.qualification import QualificationError, run_qualification
from app.services.tenant_notify import get_owner_notification_email
from app.services.workflow_runs import log_workflow_run

router = APIRouter(prefix="/v1/internal", tags=["internal"], dependencies=[Depends(verify_internal_service_token)])
settings = get_settings()


@router.get("/leads/{lead_id}", response_model=LeadResponse)
def internal_get_lead(
    lead_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    tenant_id: Annotated[UUID, Query()],
) -> LeadResponse:
    lead = lead_service.get_lead(db, tenant_id, lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return LeadResponse.model_validate(lead)


@router.post("/leads/{lead_id}/qualify", response_model=QualificationResponse)
def internal_qualify_lead(
    lead_id: UUID,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    tenant_id: Annotated[UUID, Query(description="Tenant that owns the lead")],
) -> QualificationResponse:
    lead = lead_service.get_lead(db, tenant_id, lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    try:
        row = run_qualification(db, lead=lead, actor_type=ActorType.n8n, actor_id="n8n")
        db.commit()
        db.refresh(row)
    except QualificationError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    schedule_n8n_event(
        background_tasks,
        event_type="qualification.completed",
        tenant_id=tenant_id,
        lead_id=lead_id,
        payload={"priority": row.priority.value, "intent_score": row.intent_score},
        idempotency_key=f"qualification.completed:{row.id}",
    )
    return QualificationResponse.model_validate(row)


@router.post("/leads/{lead_id}/staff-notify", response_model=StaffNotifyResponse)
def internal_staff_notify(
    lead_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    tenant_id: Annotated[UUID, Query()],
) -> StaffNotifyResponse:
    lead = lead_service.get_lead(db, tenant_id, lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    owner_email = get_owner_notification_email(db, tenant_id)
    emailed = False
    if owner_email:
        try:
            send_email(
                to_address=owner_email,
                subject=f"Hot lead: {lead.full_name}",
                body_text=(
                    f"Priority: {lead.priority.value}\n"
                    f"Name: {lead.full_name}\n"
                    f"Email: {lead.email or '—'}\n"
                    f"Phone: {lead.phone or '—'}\n\n"
                    f"Enquiry:\n{lead.enquiry_text}"
                ),
            )
            emailed = True
        except EmailDeliveryError:
            emailed = False

    record_lead_event(
        db,
        tenant_id=tenant_id,
        lead_id=lead.id,
        event_type="staff.notified",
        payload={"channel": "email" if emailed else "log", "priority": lead.priority.value},
        actor_type=ActorType.n8n,
        actor_id="n8n",
    )
    db.commit()
    msg = f"Staff notified via email ({owner_email})" if emailed else "Staff notification logged (email unavailable)"
    return StaffNotifyResponse(message=msg)


@router.post("/leads/{lead_id}/follow-ups/execute", response_model=FollowUpExecuteResponse)
def internal_execute_follow_up(
    lead_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    tenant_id: Annotated[UUID, Query()],
) -> FollowUpExecuteResponse:
    lead = lead_service.get_lead(db, tenant_id, lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    result = follow_up_service.execute_next_follow_up(db, lead)
    db.commit()
    return FollowUpExecuteResponse(lead_id=lead_id, result=result)


@router.post("/inbound-email")
def internal_inbound_email(
    payload: InboundEmailPayload,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    comm = comm_service.record_inbound_email(
        db,
        tenant_id=payload.tenant_id,
        from_email=payload.from_email,
        subject=payload.subject,
        body=payload.body,
    )
    if comm is None:
        raise HTTPException(status_code=404, detail="lead_not_found_for_email")
    db.commit()
    return {"ok": True, "lead_id": str(comm.lead_id), "communication_id": str(comm.id)}


@router.get("/follow-ups/due", response_model=list[FollowUpDueItem])
def internal_follow_ups_due(
    db: Annotated[Session, Depends(get_db)],
    tenant_id: Annotated[UUID, Query()],
    limit: int = Query(50, ge=1, le=200),
) -> list[FollowUpDueItem]:
    leads = follow_up_service.list_due_follow_ups(db, tenant_id, limit=limit)
    return [
        FollowUpDueItem(
            lead_id=lead.id,
            full_name=lead.full_name,
            email=lead.email,
            priority=lead.priority.value,
            next_follow_up_at=lead.next_follow_up_at,  # type: ignore[arg-type]
        )
        for lead in leads
        if lead.next_follow_up_at is not None
    ]


@router.get("/daily-summary", response_model=DailySummaryResponse)
def internal_daily_summary(
    db: Annotated[Session, Depends(get_db)],
    tenant_id: Annotated[UUID, Query()],
) -> DailySummaryResponse:
    overview = analytics_service.get_overview(db, tenant_id)
    record_lead_event(
        db,
        tenant_id=tenant_id,
        lead_id=None,
        event_type="daily_summary.generated",
        payload=overview,
        actor_type=ActorType.n8n,
        actor_id="n8n",
    )

    owner_email = get_owner_notification_email(db, tenant_id)
    message = "Summary generated"
    if owner_email:
        lines = [f"{k.replace('_', ' ').title()}: {v}" for k, v in overview.items()]
        try:
            send_email(
                to_address=owner_email,
                subject="LeadFlow daily sales summary",
                body_text="Good morning,\n\n" + "\n".join(lines) + "\n\n— Vyrenlo LeadFlow",
            )
            message = f"Summary emailed to {owner_email}"
            record_lead_event(
                db,
                tenant_id=tenant_id,
                lead_id=None,
                event_type="daily_summary.sent",
                payload={"email": owner_email},
                actor_type=ActorType.n8n,
                actor_id="n8n",
            )
        except EmailDeliveryError:
            message = "Summary generated (email failed)"

    db.commit()
    return DailySummaryResponse(overview=overview, message=message)


@router.post("/workflow-runs", response_model=WorkflowRunResponse, status_code=201)
def internal_log_workflow_run(
    payload: WorkflowRunCreate,
    db: Annotated[Session, Depends(get_db)],
) -> WorkflowRunResponse:
    row = log_workflow_run(db, payload)
    db.commit()
    db.refresh(row)
    return WorkflowRunResponse.model_validate(row)


@router.get("/health")
def internal_health() -> dict[str, str]:
    return {"status": "ok", "integration": "n8n"}