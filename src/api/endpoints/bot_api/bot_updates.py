import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from starlette.status import HTTP_200_OK

from src.bot.notification_sender.base import SenderInterface
from src.dependencies import get_http_sender
from src.scrapper.schemas import ApiErrorResponse, LinkUpdate

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post(
    "/updates",
    status_code=HTTP_200_OK,
    summary="Отправить обновление",
    response_description="Обновление обработано",
    responses={400: {"model": ApiErrorResponse, "description": "Некорректные параметры запроса"}},
)
async def process_link_update(
    update: LinkUpdate,
    http_sender: SenderInterface = Depends(get_http_sender),
) -> Dict[str, Any]:
    """Обрабатывает обновления ссылок, полученные от внешних источников (Scrapper)."""
    logger.info(
        "Received link update",
        extra={
            "update_id": update.id,
            "url": str(update.url),
            "chat_ids": update.tg_chat_ids,
        },
    )
    for chat_id in update.tg_chat_ids:
        await http_sender.send_notification(chat_id, str(update.url), update.model_dump())

    return {"message": "Update processed"}
