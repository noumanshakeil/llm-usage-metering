from fastapi import APIRouter
from backend.api import health, metering, ui
api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(metering.router, prefix="/api", tags=["metering"])
api_router.include_router(ui.router, tags=["ui"])
