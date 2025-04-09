from typing import Awaitable, Callable, Dict, Optional

from telethon import events

from src.bot.command_context import CommandContext
from src.handlers.help import help_handler
from src.handlers.list_links import list_links_handler
from src.handlers.start import start_handler
from src.handlers.tag_handlers import mute_tag_handler, unmute_tag_handler
from src.handlers.track import track_handler
from src.handlers.untrack import untrack_handler

HandlerType = Callable[[events.NewMessage.Event, CommandContext], Awaitable[None]]


class HandlersRegistry:
    """Registry mapping commands to their corresponding handler functions."""

    def __init__(self) -> None:
        """Initializes the registry with a mapping of commands to handlers."""
        self._handlers: Dict[str, HandlerType] = {
            "/track": track_handler,
            "/untrack": untrack_handler,
            "/list": list_links_handler,
            "/start": start_handler,
            "/help": help_handler,
            "/mute": mute_tag_handler,
            "/unmute": unmute_tag_handler,
        }

    def get(self, command: str) -> Optional[HandlerType]:
        """Retrieves the handler function for the given command.

        Args:
            command (str): Name of the command.

        Returns:
            Optional[HandlerType]: The handler function if it exists, otherwise None.

        """
        return self._handlers.get(command.lower())
