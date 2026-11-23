from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.lead import Tenant, User


def get_owner_notification_email(db: Session, tenant_id: uuid.UUID) -> str | None:
    tenant = db.get(Tenant, tenant_id)
    if tenant and tenant.settings.get("owner_email"):
        return str(tenant.settings["owner_email"])

    owner = db.scalar(
        select(User).where(User.tenant_id == tenant_id, User.role == UserRole.owner, User.is_active.is_(True))
    )
    return owner.email if owner else None