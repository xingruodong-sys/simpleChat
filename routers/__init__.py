from fastapi import APIRouter
from . import settings, dashboard, system, download, webhooks, history, statistics

api_router = APIRouter()

api_router.include_router(settings.router, prefix="/api")
api_router.include_router(dashboard.router, prefix="/api")
api_router.include_router(system.router, prefix="/api")
api_router.include_router(history.router, prefix="/api")
api_router.include_router(statistics.router, prefix="/api")
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(download.router, tags=["download"])
