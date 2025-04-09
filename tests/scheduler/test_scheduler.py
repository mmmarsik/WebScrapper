from unittest.mock import AsyncMock, MagicMock

import pytest

from src.bot.scheduler import Scheduler


class TestScheduler:
    """Tests for the Scheduler class functionality."""

    @pytest.fixture
    def scheduler_setup(self) -> Scheduler:
        """Create a basic Scheduler instance with mock dependencies.

        Returns:
            Scheduler: Configured Scheduler for testing

        """
        scrapper_client = AsyncMock()
        scrapper_client.list_links = AsyncMock(
            return_value={"links": [{"url": "http://example.com", "tags": ["example"]}]},
        )

        telegram_client = AsyncMock()
        telegram_client.send_message = AsyncMock()

        chat_repository = MagicMock()
        chat_repository.get_all_chats_ids = MagicMock(return_value=[1, 2])

        scheduler = Scheduler(
            scrapper_client=scrapper_client,
            telegram_client=telegram_client,
            chat_repository=chat_repository,
        )

        scheduler.extract_github_repo = MagicMock(return_value="")
        scheduler.extract_stackoverflow_question_id = MagicMock(return_value="")

        return scheduler

    @pytest.mark.asyncio
    async def test_check_updates_once(self, scheduler_setup: Scheduler) -> None:
        """Test that check_updates_once retrieves links for all users.

        Args:
            scheduler_setup: Configured Scheduler instance

        """
        scheduler = scheduler_setup

        links_data = {"links": [{"url": "http://example.com", "tags": ["example"]}]}
        scheduler.scrapper_client.list_links = AsyncMock(return_value=links_data)

        await scheduler.check_updates_once()

        correct_call_count = 2
        assert scheduler.scrapper_client.list_links.call_count == correct_call_count

        call_args_list = scheduler.scrapper_client.list_links.call_args_list
        called_ids = [call[0][0] for call in call_args_list]
        assert sorted(called_ids) == [1, 2]

    @pytest.mark.asyncio
    async def test_send_notification(self, scheduler_setup: Scheduler) -> None:
        """Test that send_notification correctly sends telegram messages.

        Args:
            scheduler_setup: Configured Scheduler instance

        """
        scheduler = scheduler_setup

        chat_id = 123
        message = "Test notification message"

        await scheduler.send_notification(chat_id, message)

        scheduler.telegram_client.send_message.assert_called_once_with(
            chat_id,
            "[NOTIFICATION] " + message,
            reply_to=0,
        )
