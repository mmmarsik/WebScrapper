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


def get_tag_http_error_message(e: ScrapperAPIHTTPError, tag_name: str, default_msg: str) -> str:
    """Возвращает текст ошибки в зависимости от HTTP-кода ошибки."""
    if e.status_code == HTTPStatus.BAD_REQUEST.value:
        return ErrorMessage.CHAT_NOT_REGISTERED.value
    if e.status_code == HTTPStatus.NOT_FOUND.value:
        return f"Tag '{tag_name}' not found or no links with this tag."
    return default_msg


async def mute_tag_handler(event: events.NewMessage.Event, context: CommandContext) -> None:
    """Handles the /mute_tag command.

    This command mutes a specified tag for a chat, preventing notifications
    related to that tag.

    Args:
        event: The Telegram message event.
        context: The command execution context.

    """
    chat_id = event.chat_id

    command_parts = event.text.split(maxsplit=1)

    correct_parts_count = 2
    if len(command_parts) < correct_parts_count:
        await event.reply(ErrorMessage.INVALID_MUTE_COMMAND_USAGE.value)
        return

    tag_name = command_parts[1].strip()

    try:
        logger.info("Muting tag %s for user %s", tag_name, chat_id)
        scrapper_client = context.scrapper_client
        response = await scrapper_client.mute_tag(chat_id, tag_name)

        if response.get("affected_links", 0) > 0:
            message = (
                f"Tag '{tag_name}' has been muted.\n"
                f"Affected links: {response.get('affected_links', 0)}"
            )
        else:
            message = f"No links found with the tag '{tag_name}'"
        await event.reply(message)

    except ScrapperAPIHTTPError as e:
        logger.exception("Mute tag error for user %s", chat_id)
        error_message = get_tag_http_error_message(
            e,
            tag_name,
            ErrorMessage.ERROR_PROCESSING_MUTE.value,
        )
        await event.reply(error_message)
    except ScrapperAPIRequestError:
        logger.exception("Network error muting tag for user %s", chat_id)
        await event.reply(ErrorMessage.NETWORK.value)
    except (ScrapperAPIError, Exception):
        logger.exception("Error muting tag for user %s", chat_id)
        await event.reply(ErrorMessage.ERROR_PROCESSING_MUTE.value)


async def unmute_tag_handler(event: events.NewMessage.Event, context: CommandContext) -> None:
    """Handles the /unmute_tag command.

    This command unmutes a specified tag for a chat, allowing notifications
    related to that tag to be received again.

    Args:
        event: The Telegram message event.
        context: The command execution context.

    """
    chat_id = event.chat_id

    command_parts = event.text.split(maxsplit=1)

    correct_parts_count = 2
    if len(command_parts) < correct_parts_count:
        await event.reply(ErrorMessage.INVALID_MUTE_COMMAND_USAGE.value)
        return

    tag_name = command_parts[1].strip()

    try:
        logger.info("Unmuting tag %s for user %s", tag_name, chat_id)
        scrapper_client = context.scrapper_client
        response = await scrapper_client.unmute_tag(chat_id, tag_name)

        if response.get("affected_links", 0) > 0:
            message = (
                f"Tag '{tag_name}' has been unmuted.\n"
                f"Affected links: {response.get('affected_links', 0)}"
            )
        else:
            message = f"No links found with the tag '{tag_name}'"
        await event.reply(message)

    except ScrapperAPIHTTPError as e:
        logger.exception("Unmute tag error for user %s", chat_id)
        error_message = get_tag_http_error_message(
            e,
            tag_name,
            ErrorMessage.ERROR_PROCESSING_UNMUTE.value,
        )
        await event.reply(error_message)
    except ScrapperAPIRequestError:
        logger.exception("Network error unmuting tag for user %s", chat_id)
        await event.reply(ErrorMessage.NETWORK.value)
    except (ScrapperAPIError, Exception):
        logger.exception("Error unmuting tag for user %s", chat_id)
        await event.reply(ErrorMessage.ERROR_PROCESSING_UNMUTE.value)
