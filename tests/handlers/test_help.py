from unittest.mock import patch

import pytest

from src.bot.commands import BotCommands
from src.handlers.help import help_handler
from tests.fake_objects import FakeContext, FakeEvent


@pytest.mark.asyncio
async def test_help_handler() -> None:
    """Test that help handler sends a help message with command information.

    Verifies that the handler returns a message containing command descriptions.
    """
    user_id = 3333
    event = FakeEvent(user_id, "/help")
    context = FakeContext()

    with patch.object(
        BotCommands,
        "description",
        return_value="Available commands: /command1, /command2",
    ):
        await help_handler(event, context)

    event.reply.assert_called_once()

    response = event.reply.call_args[0][0]
    assert "command" in response.lower()
