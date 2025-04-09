import logging

from telethon import events

from src.bot.command_context import CommandContext
from src.handlers.handler_utils import ErrorMessage
from src.scrapper.scrapper_exceptions import (
    ScrapperAPIError,
    ScrapperAPIHTTPError,
    ScrapperAPIRequestError,
)

logger = logging.getLogger(__name__)


async def start_handler(event: events.NewMessage.Event, context: CommandContext) -> None:
    """Handler for /start command.
    Registers the chat via POST /tg-chat/{chat_id}. On success the user receives a
    confirmation message. If any exception is raised, the user receives one unified
    error message.
    """
    user_id = event.sender_id
    try:
        logger.info("Registering chat for user %s", user_id)
        await context.scrapper_client.register_chat(user_id)
        await event.reply("✅ Chat successfully registered!")
    except ScrapperAPIHTTPError as e:
        logger.exception("HTTP error during chat registration for user %s", user_id)
        await event.reply(f"{ErrorMessage.ERROR_PROCESSING_START} (HTTP Error: {e.status_code})")
    except ScrapperAPIRequestError:
        logger.exception("Network error during chat registration for user %s", user_id)
        await event.reply("f{ErrorMessage.NETWORK}")
    except ScrapperAPIError as e:
        logger.exception("API error during chat registration for user %s", user_id)
        await event.reply(f"{ErrorMessage.ERROR_PROCESSING_START} (API Error: {e!s})")
    except Exception:
        logger.exception("Unexpected error during chat registration for user %s", user_id)
        await event.reply(ErrorMessage.ERROR_PROCESSING_START)
