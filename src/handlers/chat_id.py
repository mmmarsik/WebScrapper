import logging

from telethon import events

from src.bot.command_context import CommandContext
from src.handlers.handler_utils import ErrorMessage

__all__ = ("chat_id_cmd_handler",)

logger = logging.getLogger(__name__)


async def chat_id_cmd_handler(event: events.NewMessage.Event, _context: CommandContext) -> None:
    """Handler for /chat_id command.
    Sends the chat ID to the user.

    Args:
        event (events.NewMessage.Event): Telegram new message event
        context (CommandContext): Command execution context

    """
    try:
        logger.info("Processing /chat_id command for user %s", event.sender_id)
        await event.reply(f"🔑 Your Chat ID: {event.sender_id}")
    except Exception:
        logger.exception("Error processing /chat_id command: %s", event.sender_id)
        await event.reply(ErrorMessage.ERROR_GETTING_CHAT_ID)
