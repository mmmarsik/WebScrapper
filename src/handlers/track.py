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


async def safe_get_response(
    prompt: str,
    conv: events.NewMessage.Event,
    expected_user_id: int,
) -> str:
    """Helper function for safe conversation handling.

    Args:
        prompt (str): Message to send to user
        conv: Telethon conversation object
        expected_user_id (int): Expected user ID for response.

    Returns:
        str: Validated response text

    """
    await conv.send_message(prompt)
    while True:
        response = await conv.get_response()
        text = response.text.strip()
        if response.sender_id != expected_user_id:
            logger.debug("Ignoring response from different user: %s", response.sender_id)
            continue
        if text.startswith("[NOTIFICATION]"):
            logger.debug("Skipping notification message")
            continue
        if text.startswith("/"):
            await conv.send_message(ErrorMessage.ERROR_EXPECTED_TEXT_NOT_COMMAND)
            continue
        logger.debug("Received valid response: %s", text)
        return str(text)


async def track_handler(event: events.NewMessage.Event, context: CommandContext) -> None:
    """Handler for /track command with FSM implementation.

    Args:
        event (events.NewMessage.Event): Telegram new message event
        context (CommandContext): Command execution context

    """
    user_id = event.sender_id
    logger.info("Starting track session for user %s", user_id)

    context.session_manager.add_session(user_id, "TRACK")

    correct_parts_count = 2

    try:
        message_text = event.message.raw_text.strip()
        parts = message_text.split(maxsplit=correct_parts_count - 1)
        if len(parts) < correct_parts_count:
            await event.reply(ErrorMessage.INVALID_COMMAND_USAGE)
            return

        url = parts[1]

        if not url.startswith("http"):
            await event.reply(ErrorMessage.INVALID_COMMAND_USAGE)
            logger.error("User %s provided invalid URL to track: %s", user_id, url)
            return

        async with event.client.conversation(event.chat_id) as conv:
            tags_text = await safe_get_response(
                "📝 Enter tags (comma-separated) or 'skip'",
                conv,
                user_id,
            )
            tags = (
                [tag.strip() for tag in tags_text.split(",") if tag.strip()]
                if tags_text.lower() not in {"skip", "none"}
                else []
            )

            filters_text = await safe_get_response(
                "🔍 Enter filters (comma-separated) or 'skip'",
                conv,
                user_id,
            )
            filters = (
                [flt.strip() for flt in filters_text.split(",") if flt.strip()]
                if filters_text.lower() not in {"skip", "none"}
                else []
            )

            response = await context.scrapper_client.add_link(user_id, url, tags, filters)
            await conv.send_message(f"✅ Successfully added: {response.get('url', url)}")

    except ScrapperAPIHTTPError as e:
        logger.exception("Track error for user %s", user_id)
        if e.status_code == HTTPStatus.BAD_REQUEST.value:
            await event.reply(ErrorMessage.CHAT_NOT_REGISTERED)
        else:
            await event.reply(ErrorMessage.ERROR_PROCESSING_TRACK)
    except ScrapperAPIRequestError:
        logger.exception("Network error tracking for user %s", user_id)
        await event.reply("Network error. Please check your connection and try again.")

    except (ScrapperAPIError, Exception):
        logger.exception("Unexpected track error for user %s", user_id)
        await event.reply(ErrorMessage.ERROR_PROCESSING_TRACK)
    finally:
        context.session_manager.remove_session(user_id)
