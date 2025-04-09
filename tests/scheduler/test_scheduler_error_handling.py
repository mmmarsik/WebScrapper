from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.bot.scheduler import Scheduler


class TestSchedulerErrorHandling:
    """Tests for error handling in the Scheduler."""

    @pytest.fixture
    def error_scheduler(self) -> Scheduler:
        """Create a Scheduler instance configured for testing error handling.

        Returns:
            Scheduler: Configured for testing error scenarios

        """
        scrapper_client = AsyncMock()
        telegram_client = AsyncMock()
        chat_repository = MagicMock()
        chat_repository.get_all_chats_ids = MagicMock(return_value=[101, 102])

        scheduler = Scheduler(
            scrapper_client=scrapper_client,
            telegram_client=telegram_client,
            chat_repository=chat_repository,
        )

        scheduler.github_client = AsyncMock()
        scheduler.stackoverflow_client = AsyncMock()

        scheduler.extract_github_repo = MagicMock(return_value="owner/repo")
        scheduler.extract_stackoverflow_question_id = MagicMock(return_value="12345")
        scheduler.send_notification = AsyncMock()

        return scheduler

    @pytest.mark.asyncio
    async def test_github_update_error(self, error_scheduler: Scheduler) -> None:
        """Test that errors during GitHub update checking are handled gracefully."""
        error_scheduler.github_client.get_repo_last_updated = AsyncMock(
            side_effect=Exception("GitHub error"),
        )
        github_update = error_scheduler._check_github_update  # noqa: SLF001
        await github_update(user_id=1, url="https://github.com/owner/repo")
        cast(AsyncMock, error_scheduler.send_notification).assert_not_called()

    @pytest.mark.asyncio
    async def test_stackoverflow_update_error(self, error_scheduler: Scheduler) -> None:
        """Test that errors during StackOverflow update checking are handled gracefully."""
        error_scheduler.stackoverflow_client.get_question_last_activity = AsyncMock(
            side_effect=Exception("StackOverflow error"),
        )
        stackoverflow_update = error_scheduler._check_stackoverflow_update  # noqa: SLF001
        await stackoverflow_update(user_id=1, url="https://stackoverflow.com/questions/12345")
        cast(AsyncMock, error_scheduler.send_notification).assert_not_called()

    @pytest.mark.asyncio
    async def test_scrapper_client_error_handling(self, error_scheduler: Scheduler) -> None:
        """Test that Scrapper client errors are properly handled.

        Args:
            error_scheduler: Configured Scheduler instance

        """
        scheduler = error_scheduler

        cast(AsyncMock, scheduler.scrapper_client.list_links).side_effect = Exception("API Error")

        await scheduler.check_updates_once()

        assert len(scheduler.last_updates) == 0
        assert len(cast(AsyncMock, scheduler.send_notification).call_args_list) == 0
