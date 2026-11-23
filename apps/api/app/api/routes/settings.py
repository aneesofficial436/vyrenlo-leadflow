from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.schemas.api_keys import ApiKeyCreate, ApiKeyCreatedResponse, ApiKeyResponse
from app.services import api_keys as api_key_service

router = APIRouter(prefix="/v1/settings", tags=["settings"])


@router.get("/api-keys", response_model=list[ApiKeyResponse])
def list_keys(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_roles(UserRole.owner, UserRole.admin))],
) -> list[ApiKeyResponse]:
    keys = api_key_service.list_api_keys(db, current.tenant_id)
    return [ApiKeyResponse.model_validate(k) for k in keys]


@router.post("/api-keys", response_model=ApiKeyCreatedResponse, status_code=201)
def create_key(
    payload: ApiKeyCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[CurrentUser, Depends(require_roles(UserRole.owner, UserRole.admin))],
) -> ApiKeyCreatedResponse:
    row, plain = api_key_service.create_api_key(db, current.tenant_id, payload.name, payload.scopes)
    db.commit()
    db.refresh(row)
    base = ApiKeyResponse.model_validate(row)
    return ApiKeyCreatedResponse(**base.model_dump(), api_key=plain)