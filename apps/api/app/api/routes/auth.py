from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, TokenResponse, UserResponse
from app.services import auth_service
from app.services.rate_limit import enforce_login_rate_limit

router = APIRouter(prefix="/v1/auth", tags=["auth"])
settings = get_settings()


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    client_ip = request.client.host if request.client else "unknown"
    enforce_login_rate_limit(client_key=f"{client_ip}:{payload.tenant_slug}")
    try:
        user = auth_service.authenticate_user(
            db,
            payload.tenant_slug,
            str(payload.email).lower(),
            payload.password,
        )
        access, refresh = auth_service.issue_tokens(db, user)
        db.commit()
    except auth_service.AuthError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    try:
        access, new_refresh, _user = auth_service.refresh_access_token(db, payload.refresh_token)
        db.commit()
    except auth_service.AuthError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return TokenResponse(
        access_token=access,
        refresh_token=new_refresh,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: LogoutRequest, db: Annotated[Session, Depends(get_db)]) -> None:
    auth_service.revoke_refresh_token(db, payload.refresh_token)
    db.commit()


@router.get("/me", response_model=UserResponse)
def me(current: Annotated[CurrentUser, Depends(get_current_user)]) -> UserResponse:
    return UserResponse.model_validate(current.user)