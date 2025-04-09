from unittest.mock import AsyncMock

import pytest

from src.handlers.list_links import list_links_handler
from tests.fake_objects import FakeContext, FakeEvent


@pytest.mark.asyncio
async def test_list_handler_empty() -> None:
    """Test that list handler correctly handles empty link lists.

    Verifies that the handler sends an appropriate message when there are no tracked links.
    """
    user_id = 2222
    event = FakeEvent(user_id, "/list")
    context = FakeContext()

    context.scrapper_client.list_links = AsyncMock(return_value={"links": []})

    await list_links_handler(event, context)

    event.reply.assert_called_once()
    response = event.reply.call_args[0][0]
    assert "empty" in response.lower()


@pytest.mark.asyncio
async def test_list_handler_with_links() -> None:
    """Test that list handler correctly shows tracked links.

    Verifies that the handler displays all tracked links with their tags and filters.
    """
    user_id = 2222
    event = FakeEvent(user_id, "/list")
    context = FakeContext()

    links = [
        {
            "url": "https://github.com/example/repo1",
            "tags": ["tech", "code"],
            "filters": ["python"],
        },
        {"url": "https://stackoverflow.com/q/12345", "tags": ["qa"], "filters": []},
    ]

    context.scrapper_client.list_links = AsyncMock(return_value={"links": links})

    await list_links_handler(event, context)

    event.reply.assert_called_once()
    response = event.reply.call_args[0][0]

    for link in links:
        assert link["url"] in response

    assert "tech" in response
    assert "code" in response
    assert "qa" in response
