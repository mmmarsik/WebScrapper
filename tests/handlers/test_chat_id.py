import pytest

from src.handlers.chat_id import chat_id_cmd_handler
from tests.fake_objects import FakeContext, FakeEvent


@pytest.mark.asyncio
async def test_chat_id_cmd_handler() -> None:
    """Test that chat_id handler sends the correct chat ID to the user.

    Verifies that the handler responds with a message containing the user's chat ID.
    """
    user_id = 1234
    event = FakeEvent(user_id, "/chat_id")
    context = FakeContext()

    await chat_id_cmd_handler(event, context)

    event.reply.assert_called_once()

    response = int(event.reply.call_args[0][0].split()[-1])
    assert user_id == response
