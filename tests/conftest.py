import asyncio

import pytest


@pytest.fixture
def event_loop_policy() -> asyncio.AbstractEventLoopPolicy:
    """Return the event loop policy."""
    return asyncio.DefaultEventLoopPolicy()
