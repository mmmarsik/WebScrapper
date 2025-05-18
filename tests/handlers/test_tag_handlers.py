from typing import Dict, NoReturn

import pytest

from src.handlers.tag_handlers import mute_tag_handler, unmute_tag_handler


class FakeEvent:
    """A fake event class for testing purposes.

    Attributes:
        text (str): The text of the event.
        chat_id (int): The chat ID associated with the event.
        responses (list): A list to store the responses to the event.

    """

    def __init__(self, text: str, chat_id: int) -> None:
        """Initializes a new instance of the FakeEvent class."""
        self.text = text
        self.chat_id = chat_id
        self.responses = []

    async def reply(self, message: str) -> None:
        """Simulates replying to the event.

        Args:
            message (str): The message to reply with.

        """
        self.responses.append(message)


class TagMuteError(Exception):
    """Пользовательское исключение для ошибок при мьюте тегов."""


class FakeScrapperClient:
    """Фейковый scrapper-клиент, который симулирует успешные операции."""

    async def mute_tag(self, _chat_id: int, _tag_name: str) -> Dict[str, int]:
        """Симулирует успешное мьютирование тега."""
        return {"affected_links": 1}

    async def unmute_tag(self, _chat_id: int, _tag_name: str) -> Dict[str, int]:
        """Симулирует успешное размьютирование тега."""
        return {"affected_links": 1}


class FailingScrapperClient:
    """Фейковый scrapper-клиент, который симулирует неудачные операции."""

    async def mute_tag(self, _chat_id: int, _tag_name: str) -> NoReturn:
        """Симулирует неудачное мьютирование тега."""
        raise TagMuteError("Mute tag failed")

    async def unmute_tag(self, _chat_id: int, _tag_name: str) -> NoReturn:
        """Симулирует неудачное размьютирование тега."""
        raise TagMuteError("Unmute tag failed")


class FakeContext:
    """A fake context class for testing purposes.

    Attributes:
        scrapper_client: The fake scrapper client.

    """

    def __init__(self, scrapper_client: FakeScrapperClient) -> None:
        self.scrapper_client = scrapper_client


@pytest.mark.asyncio
async def test_mute_tag_handler_success() -> None:
    """Tests the mute_tag_handler with a successful scrapper client."""
    event = FakeEvent("/mute_tag testtag", chat_id=123)
    context = FakeContext(FakeScrapperClient())
    await mute_tag_handler(event, context)
    assert any("muted" in reply.lower() for reply in event.responses)


@pytest.mark.asyncio
async def test_unmute_tag_handler_success() -> None:
    """Tests the unmute_tag_handler with a successful scrapper client."""
    event = FakeEvent("/unmute_tag testtag", chat_id=123)
    context = FakeContext(FakeScrapperClient())
    await unmute_tag_handler(event, context)
    assert any("unmuted" in reply.lower() for reply in event.responses)


@pytest.mark.asyncio
async def test_mute_tag_handler_failure() -> None:
    """Tests the mute_tag_handler with a failing scrapper client."""
    event = FakeEvent("/mute_tag testtag", chat_id=123)
    context = FakeContext(FailingScrapperClient())
    await mute_tag_handler(event, context)
    assert any("error" in reply.lower() for reply in event.responses)


@pytest.mark.asyncio
async def test_unmute_tag_handler_failure() -> None:
    """Tests the unmute_tag_handler with a failing scrapper client."""
    event = FakeEvent("/unmute_tag testtag", chat_id=123)
    context = FakeContext(FailingScrapperClient())
    await unmute_tag_handler(event, context)
    assert any("error" in reply.lower() for reply in event.responses)


@pytest.mark.asyncio
async def test_mute_tag_handler_missing_tag() -> None:
    """Tests the mute_tag_handler when the tag is missing."""
    event = FakeEvent("/mute_tag", chat_id=123)
    context = FakeContext(FakeScrapperClient())
    await mute_tag_handler(event, context)
    assert any("usage" in reply.lower() or "error" in reply.lower() for reply in event.responses)


@pytest.mark.asyncio
async def test_unmute_tag_handler_missing_tag() -> None:
    """Tests the unmute_tag_handler when the tag is missing."""
    event = FakeEvent("/unmute_tag", chat_id=123)
    context = FakeContext(FakeScrapperClient())
    await unmute_tag_handler(event, context)
    assert any("usage" in reply.lower() or "error" in reply.lower() for reply in event.responses)
