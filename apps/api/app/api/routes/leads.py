from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_current_user, require_roles
from app.db.session import get_db
from app.models.enums import ActorType, LeadPriority, LeadStatus, UserRole
from app.schemas.leads import (
    LeadCreate,
    LeadListResponse,
    LeadNoteCreate,
    LeadNoteResponse,
    LeadResponse,
    LeadUpdate,
)
from app.schemas.qualification import LeadDetailResponse, QualificationResponse
from app.services import leads as lead_service
from app.services.n8n_dispatch import schedule_n8n_event
from app.services.qualification import (
    QualificationError,
    get_latest_qualification,
    maybe_auto_qualify,
    run_qualification,
)

router = APIRouter(prefix="/v1/leads", tags=["leads"])


@router.get("", response_model=LeadListResponse)
def list_leads(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: LeadStatus | None = None,
    priority: LeadPriority | None = None,
    search: str | None = Query(None, max_length=200),
    sort: str = Query("created_at_desc", pattern="^(created_at_desc|created_at_asc|priority_desc)$"),
) -> LeadListResponse:
    items, total = lead_service.list_leads(
        db,
        current.tenant_id,
        page=page,
        page_size=page_size,
        status=status,
        priority=priority,
        search=search,
        sort=sort,
    )
    return LeadListResponse(
        items=[LeadResponse.model_validate(lead) for lead in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(
    payload: LeadCreate,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_roles(UserRole.owner, UserRole.admin, UserRole.agent))],
) -> LeadResponse:
    if not payload.email and not payload.phone:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="email_or_phone_required")
    lead = lead_service.create_lead_manual(db, current.tenant_id, payload, str(current.id))
    qualification = maybe_auto_qualify(db, lead)
    db.commit()
    db.refresh(lead)
    schedule_n8n_event(
        background_tasks,
        event_type="lead.created",
        tenant_id=current.tenant_id,
        lead_id=lead.id,
        payload={"source": lead.source},
        idempotency_key=f"lead.created:{lead.id}",
    )
    if qualification is not None:
        schedule_n8n_event(
            background_tasks,
            event_type="qualification.completed",
            tenant_id=current.tenant_id,
            lead_id=lead.id,
            payload={"priority": qualification.priority.value},
            idempotency_key=f"qualification.completed:{qualification.id}",
        )
    return LeadResponse.model_validate(lead)


@router.get("/{lead_id}", response_model=LeadDetailResponse)
def get_lead(
    lead_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
) -> LeadDetailResponse:
    lead = lead_service.get_lead(db, current.tenant_id, lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    latest = get_latest_qualification(db, lead.id)
    return LeadDetailResponse(
        lead=LeadResponse.model_validate(lead),
        latest_qualification=QualificationResponse.model_validate(latest) if latest else None,
    )


@router.post("/{lead_id}/qualify", response_model=QualificationResponse)
def qualify_lead(
    lead_id: UUID,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_roles(UserRole.owner, UserRole.admin, UserRole.agent))],
) -> QualificationResponse:
    lead = lead_service.get_lead(db, current.tenant_id, lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    try:
        row = run_qualification(db, lead=lead, actor_type=ActorType.user, actor_id=str(current.id))
        db.commit()
        db.refresh(row)
    except QualificationError as exc:
        db.rollback()
        schedule_n8n_event(
            background_tasks,
            event_type="qualification.failed",
            tenant_id=current.tenant_id,
            lead_id=lead_id,
            payload={"reason": str(exc)},
            idempotency_key=f"qualification.failed:{lead_id}",
        )
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    schedule_n8n_event(
        background_tasks,
        event_type="qualification.completed",
        tenant_id=current.tenant_id,
        lead_id=lead.id,
        payload={"priority": row.priority.value, "intent_score": row.intent_score},
        idempotency_key=f"qualification.completed:{row.id}",
    )
    return QualificationResponse.model_validate(row)


@router.patch("/{lead_id}", response_model=LeadResponse)
def patch_lead(
    lead_id: UUID,
    payload: LeadUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_roles(UserRole.owner, UserRole.admin, UserRole.agent))],
) -> LeadResponse:
    lead = lead_service.get_lead(db, current.tenant_id, lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    lead = lead_service.update_lead(db, lead, payload, str(current.id))
    db.commit()
    db.refresh(lead)
    return LeadResponse.model_validate(lead)


@router.post("/{lead_id}/notes", response_model=LeadNoteResponse, status_code=status.HTTP_201_CREATED)
def add_note(
    lead_id: UUID,
    payload: LeadNoteCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_roles(UserRole.owner, UserRole.admin, UserRole.agent))],
) -> LeadNoteResponse:
    lead = lead_service.get_lead(db, current.tenant_id, lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    note = lead_service.add_lead_note(db, lead, payload.body, current.id)
    db.commit()
    db.refresh(note)
    return LeadNoteResponse.model_validate(note)