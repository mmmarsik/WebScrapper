from unittest.mock import AsyncMock, MagicMock

import pytest

from src.handlers.untrack import untrack_handler


@pytest.mark.asyncio
async def test_untrack_handler_success() -> None:
    """Test: when the /untrack command is correct, it should call remove_link
    and send a message about the successful removal.
    """
    user_id = 12345
    url = "https://github.com/owner/repo"

    fake_event = MagicMock()
    fake_event.sender_id = user_id
    fake_event.chat_id = user_id
    fake_event.reply = AsyncMock()

    fake_message = MagicMock()
    fake_message.raw_text = f"/untrack {url}"
    fake_event.message = fake_message

    fake_context = MagicMock()
    fake_context.session_manager = MagicMock()
    fake_context.session_manager.has_session = AsyncMock(return_value=True)

    fake_context.scrapper_client = MagicMock()
    fake_context.scrapper_client.remove_link = AsyncMock(return_value={"status": "success"})

    await untrack_handler(fake_event, fake_context)

    fake_context.scrapper_client.remove_link.assert_called_once_with(user_id, url)
    fake_event.reply.assert_called_once_with(f"🗑️ Successfully removed: {url}")


@pytest.mark.asyncio
async def test_untrack_handler_missing_url() -> None:
    """Test: if the /untrack command is missing a URL, remove_link should not be called,
    and the user should receive a message with information about the command usage.
    """
    user_id = 12345

    fake_event = MagicMock()
    fake_event.sender_id = user_id
    fake_event.chat_id = user_id
    fake_event.reply = AsyncMock()

    fake_message = MagicMock()
    fake_message.raw_text = "/untrack"
    fake_event.message = fake_message

    fake_context = MagicMock()
    fake_context.session_manager = MagicMock()
    fake_context.session_manager.has_session = AsyncMock(return_value=True)

    fake_context.scrapper_client = MagicMock()
    fake_context.scrapper_client.remove_link = AsyncMock()

    await untrack_handler(fake_event, fake_context)

    fake_context.scrapper_client.remove_link.assert_not_called()
    fake_event.reply.assert_called_once()
    response_text = fake_event.reply.call_args[0][0].lower()
    assert "usage:" in response_text


@pytest.mark.asyncio
async def test_untrack_handler_ignore_session_flag() -> None:
    """Test: even though session_manager.has_session returns False,
    the /untrack command is executed.
    """
    user_id = 12345
    url = "https://github.com/owner/repo"

    fake_event = MagicMock()
    fake_event.sender_id = user_id
    fake_event.chat_id = user_id
    fake_event.reply = AsyncMock()

    fake_message = MagicMock()
    fake_message.raw_text = f"/untrack {url}"
    fake_event.message = fake_message

    fake_context = MagicMock()
    fake_context.session_manager = MagicMock()
    fake_context.session_manager.has_session = AsyncMock(return_value=False)

    fake_context.scrapper_client = MagicMock()
    fake_context.scrapper_client.remove_link = AsyncMock(return_value={"status": "success"})

    await untrack_handler(fake_event, fake_context)

    fake_context.scrapper_client.remove_link.assert_called_once_with(user_id, url)
    fake_event.reply.assert_called_once_with(f"🗑️ Successfully removed: {url}")
