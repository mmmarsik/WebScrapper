from telethon import TelegramClient

from src.bot.settings import BotSettings
from src.scrapper.client import ScrapperAPIClient
from src.session_manager import SessionManager


class CommandContext:
    """Context passed to all command handlers.

    This includes:
      - scrapper_client: Client to interact with the Scrapper API.
      - settings: Bot configuration settings.
      - session_manager: Manager for active user sessions.
      - telegram_client: Client for communicating with Telegram.
      - bot_id: Unique identifier for the bot.
    """

    def __init__(
        self,
        scrapper_client: ScrapperAPIClient,
        settings: BotSettings,
        session_manager: SessionManager,
        telegram_client: TelegramClient,
        bot_id: int | None = None,
    ) -> None:
        """Initializes the CommandContext.

        Args:
            scrapper_client (ScrapperAPIClient): The Scrapper API client.
            settings (BotSettings): Bot settings.
            session_manager (SessionManager): Manager for user conversations.
            telegram_client (TelegramClient): Telegram client instance.
            bot_id (int | None): Bot's unique identifier. Defaults to None.

        """
        self.scrapper_client: ScrapperAPIClient = scrapper_client
        self.settings: BotSettings = settings
        self.session_manager: SessionManager = session_manager
        self.telegram_client: TelegramClient = telegram_client
        self.bot_id: int | None = bot_id
