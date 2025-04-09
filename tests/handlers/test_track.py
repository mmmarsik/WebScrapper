from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.handlers.track import track_handler
from tests.fake_objects import DummyConversation, FakeContext, FakeEvent, FakeScrapperClient


@pytest.mark.asyncio
async def test_track_handler_missing_url() -> None:
    """Test track handler when URL is missing.

    Verifies that the handler sends an error message when no URL is provided.
    """
    user_id = 1001
    event = FakeEvent(user_id, "/track")
    context = FakeContext()

    await track_handler(event, context)

    event.reply.assert_called_once()
    response = event.reply.call_args[0][0]
    assert "usage" in response.lower()
    assert "url" in response.lower()


@pytest.mark.asyncio
async def test_track_handler_active_session() -> None:
    """Test track handler when user is already in an active session.

    Verifies that the handler sends an error message when user has an active session.
    Simulates the situation where user is in the middle of /track command,
    but instead of a normal text response, they send a command (which is not allowed).
    In this case, safe_get_response raises an exception, and track_handler
    goes to the except block, sending an error message.
    """
    user_id = 1002
    event = FakeEvent(user_id, "/track https://example.com")
    event.chat_id = user_id
    context = FakeContext()

    context.session_manager.has_session = MagicMock(return_value=True)

    with patch(
        "src.handlers.track.safe_get_response",
        new=AsyncMock(side_effect=Exception("Expected text, not command")),
    ):
        await track_handler(event, context)

    event.reply.assert_called_once()
    response = event.reply.call_args[0][0]
    assert "expected text" in response.lower() or "error" in response.lower()


@pytest.mark.asyncio
async def test_track_handler_with_conversation_mock() -> None:
    """Test track handler with mocked conversation.
    Uses patching to bypass the conversation functionality.
    """
    user_id = 1003
    url = "https://github.com/example/repo"

    class MockConversation:
        def __init__(self) -> None:
            self.send_message = AsyncMock()

        async def __aenter__(self) -> "MockConversation":
            return self

        async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
            pass

    event = FakeEvent(user_id, f"/track {url}")
    event.chat_id = user_id
    event.client = MagicMock()
    event.client.conversation = lambda _chat_id: MockConversation()

    context = FakeContext()
    context.scrapper_client = MagicMock()
    context.scrapper_client.add_link = AsyncMock(
        return_value={"url": url, "tags": ["tag1", "tag2"], "filters": ["filter1", "filter2"]},
    )

    with patch("src.handlers.track.safe_get_response", new_callable=AsyncMock) as mock_get_response:
        mock_get_response.side_effect = ["tag1, tag2", "filter1, filter2"]
        await track_handler(event, context)

    context.scrapper_client.add_link.assert_called_once()
    call_args = context.scrapper_client.add_link.call_args[0]
    assert call_args[0] == user_id
    assert call_args[1] == url
    assert sorted(call_args[2]) == sorted(["tag1", "tag2"])
    assert sorted(call_args[3]) == sorted(["filter1", "filter2"])


@pytest.mark.asyncio
async def test_track_handler_calls_add_link() -> None:
    chat_id = 12345
    command_text = "/track https://github.com/owner/repo"

    fake_event = FakeEvent(sender_id=chat_id, text=command_text)
    fake_event.chat_id = chat_id
    fake_event.message.raw_text = command_text
    fake_event.client = MagicMock()
    fake_event.client.conversation = lambda _chat_id: DummyConversation()

    fake_scrapper_client = FakeScrapperClient()
    fake_scrapper_client.add_link = AsyncMock()
    fake_context = FakeContext()
    fake_context.scrapper_client = fake_scrapper_client
    fake_context.session_manager.add_session = MagicMock()

    with patch("src.handlers.track.safe_get_response", new=AsyncMock(side_effect=["skip", "skip"])):
        await track_handler(fake_event, fake_context)

    fake_scrapper_client.add_link.assert_called_once()
    call_args = fake_scrapper_client.add_link.call_args[0]
    expected_url = "https://github.com/owner/repo"
    expected_tags: list[str] = []
    expected_filters: list[str] = []

    assert call_args[0] == chat_id, f"Expected chat_id {chat_id}, got {call_args[0]}"
    assert call_args[1] == expected_url, f"Expected url {expected_url}, got {call_args[1]}"
    assert call_args[2] == expected_tags, "Expected empty list of tags"
    assert call_args[3] == expected_filters, "Expected empty list of filters"
