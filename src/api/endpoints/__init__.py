from fastapi import APIRouter

from .scrapper_api import chat, link, tag

__all__ = ("scrapper_api_router",)

scrapper_api_router = APIRouter()
scrapper_api_router.include_router(chat.chat_router)
scrapper_api_router.include_router(link.link_router)
scrapper_api_router.include_router(tag.tag_router)
