from fastapi import APIRouter

from app.api.routes import analytics, auth, communications, health, internal, leads, public, settings

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(leads.router)
api_router.include_router(communications.router)
api_router.include_router(analytics.router)
api_router.include_router(public.router)
api_router.include_router(internal.router)
api_router.include_router(settings.router)