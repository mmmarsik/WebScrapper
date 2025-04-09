import asyncio
import logging
import os

from telethon import TelegramClient

from src.bot.bot_service import BotService
from src.bot.settings import BotSettings
from src.scrapper.client import ScrapperAPIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start_bot_service() -> None:
    """Initializes and starts the Telegram bot service with its own Telethon session.
    This is a separate entry point from the FastAPI server.
    """
    api_id: int = int(os.getenv("BOT_API_ID") or 0)
    api_hash: str = os.getenv("BOT_API_HASH") or ""
    token: str = os.getenv("BOT_TOKEN") or ""

    bot_settings = BotSettings(api_id=api_id, api_hash=api_hash, token=token)

    scrapper_client = ScrapperAPIClient(base_url="http://scrapper_api:8000")

    client = TelegramClient(
        "bot_service_session",
        bot_settings.api_id,
        bot_settings.api_hash,
    )

    try:
        await client.start(bot_token=bot_settings.token)
        logger.info("BotService Telegram client started with session 'bot_service_session'")

        bot_service = BotService(
            settings=bot_settings,
            scrapper_client=scrapper_client,
            telegram_client=client,
        )

        await bot_service.start()

        await client.run_until_disconnected()
    except Exception:
        logger.exception("Error starting bot service: %s")
    finally:
        await scrapper_client.close()
        await client.disconnect()
        logger.info("Bot service stopped")


if __name__ == "__main__":
    """
    Entry point for running the bot service independently from the FastAPI application.
    This creates a separate Telethon session for handling bot commands.
    """
    try:
        asyncio.run(start_bot_service())
    except KeyboardInterrupt:
        logger.info("Bot service stopped by user")
