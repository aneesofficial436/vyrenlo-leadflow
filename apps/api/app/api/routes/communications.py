from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_current_user, require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.lead import Communication
from app.schemas.communications import CommunicationResponse
from app.services import communications as comm_service
from app.services.communications import CommunicationError

router = APIRouter(prefix="/v1/communications", tags=["communications"])


@router.get("/pending-approval", response_model=list[CommunicationResponse])
def pending_approval(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
) -> list[CommunicationResponse]:
    rows = comm_service.list_pending_approvals(db, current.tenant_id)
    return [CommunicationResponse.model_validate(r) for r in rows]


@router.get("/leads/{lead_id}", response_model=list[CommunicationResponse])
def lead_communications(
    lead_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(get_current_user)],
) -> list[CommunicationResponse]:
    return [
        CommunicationResponse.model_validate(r)
        for r in comm_service.list_communications_for_lead(db, current.tenant_id, lead_id)
    ]


@router.post("/{communication_id}/approve", response_model=CommunicationResponse)
def approve(
    communication_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_roles(UserRole.owner, UserRole.admin, UserRole.agent))],
) -> CommunicationResponse:
    comm = db.get(Communication, communication_id)
    if comm is None or comm.tenant_id != current.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    try:
        comm = comm_service.approve_communication(db, comm, current.id)
        db.commit()
        db.refresh(comm)
    except CommunicationError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CommunicationResponse.model_validate(comm)


@router.post("/{communication_id}/send", response_model=CommunicationResponse)
def send(
    communication_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_roles(UserRole.owner, UserRole.admin, UserRole.agent))],
) -> CommunicationResponse:
    comm = db.get(Communication, communication_id)
    if comm is None or comm.tenant_id != current.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    try:
        comm = comm_service.send_communication(db, comm, actor_id=str(current.id))
        db.commit()
        db.refresh(comm)
    except CommunicationError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CommunicationResponse.model_validate(comm)