import logging

from telethon import events

from src.bot.command_context import CommandContext
from src.bot.commands import BotCommands
from src.handlers.handler_utils import ErrorMessage

logger = logging.getLogger(__name__)


async def help_handler(event: events.NewMessage.Event, _context: CommandContext) -> None:
    """Handler for /help command.
    Sends the list of available commands to the user.

    Args:
        event (events.NewMessage.Event): Telegram new message event
        context (CommandContext): Command execution context

    """
    try:
        logger.info("Sending help to user %s", event.sender_id)
        await event.reply(BotCommands.description())
    except Exception:
        logger.exception("Error processing /help command for user %s", event.sender_id)
        await event.reply(ErrorMessage.ERROR_PROCESSING_HELP)
