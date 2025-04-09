import logging
from typing import TYPE_CHECKING, Optional

from telethon import TelegramClient, events
from telethon.tl.functions.bots import SetBotCommandsRequest
from telethon.tl.types import BotCommand, BotCommandScopeDefault

from src.bot.command_context import CommandContext
from src.bot.commands import BotCommands
from src.bot.handlers_registry import HandlersRegistry
from src.bot.settings import BotSettings
from src.scrapper.client import ScrapperAPIClient
from src.session_manager import SessionManager

if TYPE_CHECKING:
    from telethon.tl.custom import Message

logger = logging.getLogger(__name__)


class BotService:
    """Service for managing the Telegram bot using Telethon.

    This class creates required dependencies, registers handlers,
    and starts processing incoming events.
    """

    def __init__(
        self,
        settings: BotSettings,
        scrapper_client: ScrapperAPIClient,
        telegram_client: TelegramClient,
    ) -> None:
        """Initializes the BotService.

        Args:
            settings (BotSettings): Bot configuration settings.
            scrapper_client (ScrapperAPIClient): Client for Scrapper API.
            telegram_client: Instance of Telethon's TelegramClient.

        """
        self.settings: BotSettings = settings
        self.telegram_client = telegram_client
        self.scrapper_client: ScrapperAPIClient = scrapper_client
        self.session_manager = SessionManager()
        self.command_context = CommandContext(
            scrapper_client,
            settings,
            self.session_manager,
            telegram_client,
        )
        self.handlers_registry = HandlersRegistry()
        self.bot_id: Optional[int] = None

    async def _register_bot_commands(self) -> None:
        """Gathers all bot commands and registers them via Telegram.

        Returns:
            None

        """
        commands_list = []
        for cmd in BotCommands:
            description = cmd.current_command_description()
            command_str = cmd.value
            commands_list.append(BotCommand(command_str, description))

        try:
            await self.telegram_client(
                SetBotCommandsRequest(
                    scope=BotCommandScopeDefault(),
                    lang_code="",
                    commands=commands_list,
                ),
            )
            logger.info("Bot commands registered", extra={"commands_count": len(commands_list)})
        except Exception as exc:
            logger.exception("Error registering bot commands", extra={"error": str(exc)})

    async def start(self) -> None:
        """Starts the bot service by registering event handlers, bot commands,
        and beginning the processing of events.

        Returns:
            None

        """
        me = await self.telegram_client.get_me()
        self.bot_id = me.id
        self.command_context.bot_id = self.bot_id

        await self._register_bot_commands()
        logger.info("Bot commands registration completed", extra={})

        self.telegram_client.add_event_handler(
            self.on_new_message,
            events.NewMessage(incoming=True),
        )
        logger.info("Message handler registered", extra={"bot_id": self.bot_id})

        await self.telegram_client.run_until_disconnected()

    async def on_new_message(self, event: events.NewMessage.Event) -> None:
        """Processes an incoming message event. Ignores messages sent by the bot.

        Args:
            event (events.NewMessage.Event): The incoming message event.

        Returns:
            None

        """
        message: Message = event.message
        logger.info(
            "New message received",
            extra={
                "sender_id": message.sender_id,
                "text": message.raw_text,
            },
        )
        if message.sender_id and message.sender_id == self.bot_id:
            logger.debug(
                "Ignoring message from bot",
                extra={"message_id": getattr(message, "tg_id", None)},
            )
            return

        text = message.raw_text.strip()
        user_id = event.sender_id
        if not text:
            logger.debug("Empty message received", extra={"user_id": user_id})
            return

        if self.session_manager.has_session(user_id):
            logger.debug("User already in an active session", extra={"user_id": user_id})
            return

        command = text.split()[0].lower()
        handler = self.handlers_registry.get(command)
        if handler:
            try:
                await handler(event, self.command_context)
            except Exception as error:
                logger.exception(
                    "Error processing command",
                    extra={"user_id": user_id, "error": str(error)},
                )
        else:
            await message.reply("Unknown command. Try /help.")
