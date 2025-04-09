from fastapi import APIRouter

from . import ping
from .endpoints.bot_api.bot_updates import router as bot_updates_router

__all__ = ("router", "bot_updates_router")

router = APIRouter()
router.include_router(ping.router, tags=["ping"])
