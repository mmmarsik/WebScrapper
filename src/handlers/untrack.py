import logging

from telethon import events

from src.bot.command_context import CommandContext
from src.handlers.handler_utils import ErrorMessage
from src.http_constants import HTTPStatus
from src.scrapper.scrapper_exceptions import (
    ScrapperAPIError,
    ScrapperAPIHTTPError,
    ScrapperAPIRequestError,
)

logger = logging.getLogger(__name__)


async def untrack_handler(event: events.NewMessage.Event, context: CommandContext) -> None:
    """Handler for /untrack command.
    Removes link tracking via DELETE /links.

    Args:
        event (events.NewMessage.Event): Telegram new message event
        context (CommandContext): Command execution context

    """
    user_id = event.sender_id
    logger.info("Processing untrack for user %s", user_id)

    correct_parts_count = 2

    message_text = event.message.raw_text.strip()
    parts = message_text.split(maxsplit=correct_parts_count - 1)
    if len(parts) < correct_parts_count:
        await event.reply(ErrorMessage.INVALID_COMMAND_USAGE)
        return

    url = parts[1]

    if not url.startswith("http"):
        await event.reply(ErrorMessage.INVALID_COMMAND_USAGE)
        return

    try:
        await context.scrapper_client.remove_link(user_id, url)
        await event.reply(f"🗑️ Successfully removed: {url}")
    except ScrapperAPIHTTPError as e:
        logger.exception("Untrack error for user %s", user_id)
        if e.status_code == HTTPStatus.BAD_REQUEST.value:
            await event.reply(ErrorMessage.CHAT_NOT_REGISTERED)
        elif e.status_code == HTTPStatus.NOT_FOUND.value:
            await event.reply(ErrorMessage.LINK_NOT_FOUND)
        else:
            await event.reply(ErrorMessage.ERROR_REMOVING_LINK)
    except ScrapperAPIRequestError:
        logger.exception("Network error untracking for user %s", user_id)
        await event.reply("Network error. Please check your connection and try again.")

    except (ScrapperAPIError, Exception):
        logger.exception("Untrack error for user %s", user_id)
        await event.reply(ErrorMessage.ERROR_PROCESSING_UNTRACK)
