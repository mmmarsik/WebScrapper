import logging
from enum import StrEnum

logger = logging.getLogger(__name__)


class BotCommands(StrEnum):
    """Available bot commands."""

    START = "start"
    HELP = "help"
    TRACK = "track"
    UNTRACK = "untrack"
    LIST = "list"
    MUTE = "mute"
    UNMUTE = "unmute"

    def current_command_description(self) -> str:
        """Returns the description for the current command.

        Returns:
            str: Description message.

        """
        match self:
            case BotCommands.START:
                return "Register in the bot"
            case BotCommands.HELP:
                return "Show help message"
            case BotCommands.TRACK:
                return "Start tracking a new link"
            case BotCommands.UNTRACK:
                return "Stop tracking a link"
            case BotCommands.LIST:
                return "List all tracked links"
            case BotCommands.MUTE:
                return "Mute links with current tag"
            case BotCommands.UNMUTE:
                return "Unmute links with current tag"
            case _:
                return "Unknown command"

    @classmethod
    def description(cls) -> str:
        """Generates a formatted description for all available commands.

        Returns:
            str: Joined descriptions for all commands.

        """
        descriptions = [
            f"/{command.value} - {command.current_command_description()}" for command in cls
        ]
        return "\n".join(descriptions)
