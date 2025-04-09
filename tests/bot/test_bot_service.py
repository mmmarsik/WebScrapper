from typing import Any, Awaitable, Callable, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.bot.bot_service import BotService
from src.bot.settings import BotSettings
from src.scrapper.client import ScrapperAPIClient


class FakeTelegramClient:
    """Mock implementation of TelegramClient for testing."""

    async def get_me(self) -> object:
        """Return a fake bot user with tg_id."""

        class Me:
            tg_id = 999

        return Me()

    def add_event_handler(
        self,
        handler: Callable[[Any], Awaitable[None]],
        _event_filter: object,
    ) -> None:
        """Store the handler for testing."""
        self.handler = handler


class FakeScrapperClient(ScrapperAPIClient):
    """Mock implementation of ScrapperAPIClient for testing."""

    def __init__(self, base_url: str) -> None:
        self.base_url: str = base_url
        self.add_link_called = False
        self.add_link_params: Optional[tuple[int, str, list[str], list[str]]] = None
        self.register_chat = AsyncMock()
        self.remove_link = AsyncMock()

    async def add_link(
        self,
        _chat_id: int,
        url: str,
        tags: list[str],
        filters: list[str],
    ) -> dict[str, Any]:
        """Mock implementation of add_link method."""
        self.add_link_called = True
        self.add_link_params = (_chat_id, url, tags, filters)
        return {"url": url, "tags": tags, "filters": filters}

    async def remove_link(self, _chat_id: int, url: str) -> dict[str, Any]:
        """Mock implementation of remove_link method."""
        return {"url": url, "status": "removed"}


class FakeBotSettings(BotSettings):
    """Mock implementation of BotSettings for testing."""

    def __init__(self) -> None:
        super().__init__(api_id=12345, api_hash="fake_hash", token="fake_token")  # noqa: S106


@pytest.mark.asyncio
async def test_bot_service_initialization() -> None:
    """Test that BotService initializes correctly with all dependencies.

    Verifies that service components are properly set up and command handlers
    are registered in the handlers registry.
    """
    fake_settings = FakeBotSettings()
    fake_scrapper_client = FakeScrapperClient(base_url="https://example.com")
    fake_telegram_client = AsyncMock()

    service = BotService(
        settings=fake_settings,
        scrapper_client=fake_scrapper_client,
        telegram_client=fake_telegram_client,
    )

    assert service is not None
    assert service.scrapper_client == fake_scrapper_client
    assert service.telegram_client == fake_telegram_client
    assert service.session_manager is not None
    assert service.command_context is not None
    assert service.handlers_registry is not None

    assert service.handlers_registry.get("/start") is not None
    assert service.handlers_registry.get("/help") is not None
    assert service.handlers_registry.get("/track") is not None
    assert service.handlers_registry.get("/untrack") is not None
    assert service.handlers_registry.get("/list") is not None
    assert service.handlers_registry.get("/chat_id") is not None


@pytest.mark.asyncio
async def test_bot_unknown_command_handler() -> None:
    """Test that BotService properly handles unknown commands.

    Verifies that when a user sends an unknown command, the bot responds
    with an appropriate error message.
    """
    fake_settings = FakeBotSettings()
    fake_scrapper_client = FakeScrapperClient(base_url="https://example.com")
    fake_telegram_client = AsyncMock()

    service = BotService(
        settings=fake_settings,
        scrapper_client=fake_scrapper_client,
        telegram_client=fake_telegram_client,
    )

    fake_event = AsyncMock()
    fake_event.sender_id = 12345
    fake_event.chat_id = 12345

    fake_message = AsyncMock()
    fake_message.raw_text = "/unknown_command"
    fake_message.sender_id = 12345
    fake_message.reply = AsyncMock()

    fake_event.message = fake_message
    service.bot_id = 9999
    service.session_manager.has_session = MagicMock(return_value=False)

    await service.on_new_message(fake_event)

    fake_message.reply.assert_called_once()
    response = fake_message.reply.call_args[0][0]
    assert "unknown command" in response.lower() or "try /help" in response.lower()


@pytest.mark.asyncio
async def test_bot_regular_message_handler() -> None:
    """Test that BotService processes regular messages (not commands) as unknown commands.

    Verifies that when a user sends a message that isn't a command, the bot responds
    with the unknown command message.
    """
    fake_settings = FakeBotSettings()
    fake_scrapper_client = FakeScrapperClient(base_url="https://example.com")
    fake_telegram_client = AsyncMock()

    service = BotService(
        settings=fake_settings,
        scrapper_client=fake_scrapper_client,
        telegram_client=fake_telegram_client,
    )

    fake_event = AsyncMock()
    fake_event.sender_id = 12345
    fake_event.chat_id = 12345

    fake_message = AsyncMock()
    fake_message.raw_text = "Regular message without command"
    fake_message.sender_id = 12345
    fake_message.reply = AsyncMock()

    fake_event.message = fake_message
    service.bot_id = 9999
    service.session_manager.has_session = MagicMock(return_value=False)

    await service.on_new_message(fake_event)

    fake_message.reply.assert_called_once()


@pytest.mark.asyncio
async def test_bot_active_session_handler() -> None:
    """Test that BotService skips messages for users with active sessions.

    Verifies that when a user with an active session sends a message,
    the message is not processed by the command handlers.
    """
    fake_settings = FakeBotSettings()
    fake_scrapper_client = FakeScrapperClient(base_url="https://example.com")
    fake_telegram_client = AsyncMock()

    service = BotService(
        settings=fake_settings,
        scrapper_client=fake_scrapper_client,
        telegram_client=fake_telegram_client,
    )

    user_id = 12345
    service.session_manager.has_session = MagicMock(return_value=True)

    fake_event = AsyncMock()
    fake_event.sender_id = user_id
    fake_event.chat_id = user_id

    fake_message = AsyncMock()
    fake_message.raw_text = "Message in active session"
    fake_message.sender_id = user_id
    fake_message.reply = AsyncMock()

    fake_event.message = fake_message
    service.bot_id = 9999

    await service.on_new_message(fake_event)

    fake_message.reply.assert_not_called()
