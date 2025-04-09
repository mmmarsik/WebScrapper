from datetime import datetime, timedelta, timezone
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.bot.scheduler import Scheduler


class TestSchedulerNotifications:
    """Tests for notification functionality in the Scheduler."""

    @pytest.fixture
    def scheduler_with_mocks(self) -> Scheduler:
        """Create a Scheduler instance with mock dependencies.

        Returns:
            Scheduler: Configured for testing notifications

        """
        scrapper_client = AsyncMock()
        telegram_client = AsyncMock()
        chat_repository = MagicMock()
        chat_repository.get_all_chats_ids = MagicMock(return_value=[101, 102])
        telegram_client.send_message = AsyncMock()

        return Scheduler(scrapper_client, telegram_client, chat_repository)

    @pytest.mark.asyncio
    async def test_send_notification(self, scheduler_with_mocks: Scheduler) -> None:
        """Test that send_notification correctly sends messages.

        Args:
            scheduler_with_mocks: Configured Scheduler instance

        """
        user_id = 12345
        message = "Test notification"

        await scheduler_with_mocks.send_notification(user_id, message)

        scheduler_with_mocks.telegram_client.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_to_multiple_users(
        self,
        scheduler_with_mocks: Scheduler,
    ) -> None:
        """Test that notifications are sent to all tracking users.

        Args:
            scheduler_with_mocks: Configured Scheduler instance

        """
        users = [101, 102, 103]
        message = "Update for all users"

        for user_id in users:
            await scheduler_with_mocks.send_notification(user_id, message)

        assert scheduler_with_mocks.telegram_client.send_message.call_count == len(users)

    @pytest.mark.asyncio
    async def test_targeted_notifications(self, scheduler_with_mocks: Scheduler) -> None:
        """Test that updates are only sent to users tracking the updated link.

        Args:
            scheduler_with_mocks: Configured Scheduler instance

        """
        old_time = datetime.now(timezone.utc) - timedelta(days=1)
        new_time = datetime.now(timezone.utc)

        cast(MagicMock, scheduler_with_mocks.chat_repository.get_all_chats_ids).return_value = [101]

        scheduler_with_mocks.scrapper_client.list_links = AsyncMock()
        scheduler_with_mocks.scrapper_client.list_links.return_value = {
            "links": [{"url": "https://github.com/owner1/repo1"}],
        }

        scheduler_with_mocks.github_client = AsyncMock()
        scheduler_with_mocks.github_client.get_repo_last_updated.return_value = new_time

        scheduler_with_mocks.extract_github_repo = lambda url: (
            "owner1/repo1" if "owner1/repo1" in url else ""
        )

        scheduler_with_mocks.send_notification = AsyncMock()

        scheduler_with_mocks.last_updates = {(101, "https://github.com/owner1/repo1"): old_time}

        await scheduler_with_mocks.check_updates_once()

        scheduler_with_mocks.send_notification.assert_called_once()
        call_args = scheduler_with_mocks.send_notification.call_args

        user_1_id = 101
        assert (
            call_args[0][0] == user_1_id
        ), f"Notification sent to user {call_args[0][0]}, not {user_1_id}"
