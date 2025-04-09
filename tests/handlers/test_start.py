from typing import cast
from unittest.mock import AsyncMock

import pytest

from src.handlers.start import start_handler
from tests.fake_objects import FakeContext, FakeEvent


@pytest.mark.asyncio
async def test_start_handler() -> None:
    """Test that start handler registers new chat and sends welcome message.

    Verifies that the handler calls register_chat method with correct user ID
    and sends a welcome message with commands info.
    """
    user_id = 5555
    event = FakeEvent(user_id, "/start")
    context = FakeContext()

    await start_handler(event, context)

    cast(AsyncMock, context.scrapper_client.register_chat).assert_called_once()
    call_args = cast(AsyncMock, context.scrapper_client.register_chat).call_args[0]
    assert call_args[0] == user_id, f"Wrong user_id: {call_args[0]}, expected {user_id}"

    event.reply.assert_called_once()
    response = event.reply.call_args[0][0]
    assert "registered" in response.lower(), f"Response doesn't contain 'registered': {response}"
