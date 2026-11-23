import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.security import SecurityHeadersMiddleware

settings = get_settings()

logging.basicConfig(level=settings.log_level)

docs_url = "/docs" if settings.expose_openapi else None
redoc_url = "/redoc" if settings.expose_openapi else None
openapi_url = "/openapi.json" if settings.expose_openapi else None

app = FastAPI(
    title="Vyrenlo AI LeadFlow API",
    description="Lead management, qualification, and automation backend",
    version="0.1.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
)

if settings.trusted_host_list:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_host_list)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIdMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Api-Key", "Idempotency-Key", "X-Request-ID"],
)

app.include_router(api_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "Vyrenlo AI LeadFlow", "docs": "/docs" if settings.expose_openapi else "disabled"}