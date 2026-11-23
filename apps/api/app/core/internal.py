from typing import Annotated

from fastapi import Header, HTTPException, status

from app.core.config import get_settings

settings = get_settings()


def verify_internal_service_token(
    x_service_token: Annotated[str | None, Header(alias="X-Service-Token")] = None,
) -> None:
    if not x_service_token or x_service_token != settings.internal_service_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")