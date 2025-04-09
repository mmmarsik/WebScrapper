from datetime import datetime, timezone
from typing import Any, Dict, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bot.scheduler import Scheduler


class TestSchedulerUpdates:
    """Tests for the update checking functionality in Scheduler."""

    @pytest.fixture
    def scheduler_setup(self) -> Scheduler:
        """Create a Scheduler instance configured for testing updates.

        Returns:
            Scheduler: Configured for testing update checks

        """
        scrapper_client = AsyncMock()

        repo_data = {
            "links": [
                {
                    "url": "https://github.com/owner/repo",
                    "tags": ["github"],
                    "filters": [],
                    "type": "repository",
                    "last_commit": "2023-01-01T12:00:00Z",
                },
            ],
        }

        so_data = {
            "links": [
                {
                    "url": "https://stackoverflow.com/questions/12345/title",
                    "tags": ["stackoverflow"],
                    "filters": [],
                    "type": "question",
                    "last_activity": "2023-01-01T12:00:00Z",
                },
            ],
        }

        async def list_links_side_effect(chat_id: int) -> Dict[str, Any]:
            if chat_id % 2 == 1:
                return repo_data
            else:
                return so_data

        cast(AsyncMock, scrapper_client.list_links).side_effect = list_links_side_effect

        telegram_client = AsyncMock()
        telegram_client.send_message = AsyncMock()

        chat_repository = MagicMock()
        chat_repository.get_all_chats_ids = MagicMock(return_value=[101, 102])

        scheduler = Scheduler(
            scrapper_client=scrapper_client,
            telegram_client=telegram_client,
            chat_repository=chat_repository,
        )

        scheduler.send_notification = AsyncMock()

        scheduler.last_updates = {}

        return scheduler

    @pytest.mark.asyncio
    async def test_initial_check_updates(self, scheduler_setup: Scheduler) -> None:
        """Test that the initial update check doesn't send notifications.

        Args:
            scheduler_setup: Configured Scheduler instance

        """
        scheduler = scheduler_setup

        with patch.object(scheduler, "send_notification", new_callable=AsyncMock) as mock_notify:
            await scheduler.check_updates_once()

            mock_notify.assert_not_called()

    @pytest.mark.asyncio
    async def test_updates_detection(self, scheduler_setup: Scheduler) -> None:
        """Test that updates are properly detected and notifications sent.

        Args:
            scheduler_setup: Configured Scheduler instance

        """
        scheduler = scheduler_setup

        new_time = datetime(2023, 1, 2, tzinfo=timezone.utc)

        scheduler.github_client.get_repo_last_updated = AsyncMock(return_value=new_time)
        scheduler.stackoverflow_client.get_question_last_activity = AsyncMock(return_value=new_time)

        github_link = {"url": "https://github.com/owner/repo"}
        so_link = {"url": "https://stackoverflow.com/questions/12345"}

        scheduler.scrapper_client.list_links = AsyncMock(
            return_value={"links": [github_link, so_link], "size": 2},
        )

        with (
            patch.object(scheduler, "extract_github_repo", return_value="owner/repo"),
            patch.object(scheduler, "extract_stackoverflow_question_id", return_value="12345"),
            patch.object(scheduler, "send_notification", new_callable=AsyncMock) as mock_notify,
        ):
            await scheduler.check_updates_once()
            assert (
                mock_notify.call_count > 0
            ), "Notification was not sent, but update should have been detected"

    @pytest.mark.asyncio
    async def test_updates_sent_only_to_tracking_users(self, scheduler_setup: Scheduler) -> None:
        """Test that updates are only sent to users tracking the specific links."""
        scheduler = scheduler_setup

        user_id_1 = 101

        async def list_links_side_effect_func(user_id: int) -> Dict[str, Any]:
            if user_id == user_id_1:
                return {"links": [{"url": "https://github.com/owner/repo"}]}
            else:
                return {"links": [{"url": "https://stackoverflow.com/questions/12345/title"}]}

        cast(AsyncMock, scheduler.scrapper_client.list_links).side_effect = (
            list_links_side_effect_func
        )

        old_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        scheduler.last_updates = {(user_id_1, "https://github.com/owner/repo"): old_time}

        new_time = datetime(2023, 1, 2, tzinfo=timezone.utc)

        scheduler.github_client.get_repo_last_updated = AsyncMock(return_value=new_time)
        scheduler.stackoverflow_client.get_question_last_activity = AsyncMock(return_value=new_time)

        scheduler.send_notification = AsyncMock()

        await scheduler.check_updates_once()

        calls = scheduler.send_notification.call_args_list
        user_notifications: Dict[int, list[str]] = {}
        for call in calls:
            user_id, message = call[0]
            user_notifications.setdefault(user_id, []).append(message)

        assert any(
            "github.com" in msg for msg in user_notifications.get(user_id_1, [])
        ), "User 101 did not receive a notification about GitHub updates"
