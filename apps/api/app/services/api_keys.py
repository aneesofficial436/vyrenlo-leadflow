from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import api_key_prefix, generate_api_key_plain, hash_api_key
from app.models.lead import ApiKey


def create_api_key(db: Session, tenant_id: uuid.UUID, name: str, scopes: list[str]) -> tuple[ApiKey, str]:
    plain = generate_api_key_plain()
    row = ApiKey(
        tenant_id=tenant_id,
        name=name,
        key_prefix=api_key_prefix(plain),
        key_hash=hash_api_key(plain),
        scopes=scopes,
    )
    db.add(row)
    db.flush()
    return row, plain


def list_api_keys(db: Session, tenant_id: uuid.UUID) -> list[ApiKey]:
    return list(
        db.scalars(
            select(ApiKey).where(ApiKey.tenant_id == tenant_id).order_by(ApiKey.created_at.desc())
        ).all()
    )