from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token_plain,
    hash_token,
    verify_password,
)
from app.models.lead import RefreshToken, Tenant, User

settings = get_settings()


class AuthError(Exception):
    pass


def authenticate_user(db: Session, tenant_slug: str, email: str, password: str) -> User:
    tenant = db.scalar(select(Tenant).where(Tenant.slug == tenant_slug))
    if tenant is None:
        raise AuthError("invalid_credentials")

    user = db.scalar(
        select(User).where(
            User.tenant_id == tenant.id,
            User.email == email.strip().lower(),
            User.is_active.is_(True),
        )
    )
    if user is None or not verify_password(password, user.password_hash):
        raise AuthError("invalid_credentials")

    user.last_login_at = datetime.now(UTC)
    return user


def issue_tokens(db: Session, user: User) -> tuple[str, str]:
    access = create_access_token(user_id=user.id, tenant_id=user.tenant_id, role=user.role.value)
    refresh_plain = create_refresh_token_plain()
    refresh = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_plain),
        expires_at=datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days),
    )
    db.add(refresh)
    return access, refresh_plain


def refresh_access_token(db: Session, refresh_plain: str) -> tuple[str, str, User]:
    token_hash = hash_token(refresh_plain)
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if row is None or row.revoked_at is not None:
        raise AuthError("invalid_refresh_token")
    if row.expires_at < datetime.now(UTC):
        raise AuthError("expired_refresh_token")

    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        raise AuthError("invalid_refresh_token")

    row.revoked_at = datetime.now(UTC)
    access, new_refresh = issue_tokens(db, user)
    return access, new_refresh, user


def revoke_refresh_token(db: Session, refresh_plain: str) -> None:
    token_hash = hash_token(refresh_plain)
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if row and row.revoked_at is None:
        row.revoked_at = datetime.now(UTC)