from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

from src.bot.command_context import CommandContext
from src.bot.settings import BotSettings
from src.scrapper.client import ScrapperAPIClient
from src.session_manager import SessionManager

FakeResponse = Dict[str, Any]


class FakeMessage:
    """Mock implementation of a Telegram message for testing."""

    def __init__(self, sender_id: int, text: str) -> None:
        self.sender_id: int = sender_id
        self.text: str = text
        self.raw_text: str = text
        self.reply: AsyncMock = AsyncMock()

        class FakeSender:
            def __init__(self, tg_id: int) -> None:
                self.tg_id: int = tg_id

        self.sender = FakeSender(sender_id)


class FakeEvent:
    """Mock implementation of a Telegram event for testing handlers."""

    def __init__(self, sender_id: int, text: str) -> None:
        self.sender_id: int = sender_id
        self.text: str = text
        self.message: FakeMessage = FakeMessage(sender_id, text)
        self.chat_id: int = sender_id
        self.client: Any = None
        self.reply: AsyncMock = AsyncMock()


class FakeSessionManager(SessionManager):
    """Fake session manager for handling command sessions in tests."""

    def add_session(self, _user_id: int, _session_type: str) -> None:
        pass

    def remove_session(self, _user_id: int) -> None:
        pass

    def has_session(self, _user_id: int) -> bool:
        return False


class FakeScrapperClient(ScrapperAPIClient):
    """Fake scrapper client for testing the tracking of links."""

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url: str = base_url if base_url is not None else ""
        self.add_link_called: bool = False
        self.add_link_params: Optional[tuple[int, str, List[str], List[str]]] = None
        self.register_chat = AsyncMock()
        self.remove_link = AsyncMock()

    async def add_link(
        self,
        user_id: int,
        url: str,
        tags: List[str],
        filters: List[str],
    ) -> Dict[str, Any]:
        self.add_link_called = True
        self.add_link_params = (user_id, url, tags, filters)
        return {"status": "success", "url": url}


class DummyConversation:
    """Dummy conversation object for simulating conversation context."""

    async def __aenter__(self) -> "DummyConversation":
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass

    async def send_message(self, message: str) -> None:
        pass


class FakeBotSettings(BotSettings):
    """Fake bot settings for testing purposes."""

    def __init__(self) -> None:
        super().__init__(api_id=0, api_hash="", token="fake_token")  # noqa: S106


class FakeContext(CommandContext):
    """Fake context for testing, inheriting from CommandContext."""

    def __init__(self) -> None:
        dummy_scrapper_client = FakeScrapperClient()
        dummy_settings = FakeBotSettings()
        dummy_session_manager = FakeSessionManager()
        dummy_telegram_client = MagicMock()
        super().__init__(
            dummy_scrapper_client,
            dummy_settings,
            dummy_session_manager,
            dummy_telegram_client,
            None,
        )
        self.scrapper_client = dummy_scrapper_client
        self.session_manager = dummy_session_manager


class FakeClient:
    def conversation(self, chat_id: int) -> "FakeConversation":
        responses: List[Dict[str, Any]] = [
            {"tags": "news,tech", "chat_id": chat_id},
            {"tags": "python", "chat_id": chat_id},
        ]
        return FakeConversation(chat_id, responses)


class FakeConversation:
    def __init__(self, chat_id: int, responses: List[Dict[str, Any]]) -> None:
        self.chat_id: int = chat_id
        self.responses: List[Dict[str, Any]] = responses

    async def __aenter__(self) -> "FakeConversation":
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass

    async def send_message(self, message: str) -> None:
        pass


class FakeEventWithClient(FakeEvent):
    """Extension of FakeEvent that handles user conversation for testing."""

    def __init__(self, sender_id: int, text: str) -> None:
        """Initialize with conversation simulation capabilities.

        Args:
            sender_id: User ID
            text: Message text

        """
        super().__init__(sender_id, text)
        self._conversation_responses = {"Enter tags": "news,tech", "Enter filters": "python"}
        self._next_response_index = 0

    async def respond(self, text: str) -> "FakeEventWithClient":
        """Simulate user response in conversation.

        Args:
            text: Bot message text

        Returns:
            Self for chaining

        """
        for prompt, response in self._conversation_responses.items():
            if prompt in text:
                return FakeEventWithClient(self.sender_id, response)

        return FakeEventWithClient(self.sender_id, "")
