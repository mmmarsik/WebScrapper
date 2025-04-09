from unittest.mock import AsyncMock, MagicMock

import pytest

from src.bot.scheduler import Scheduler


class TestLinkParsing:
    """Tests for checking correct link parsing in the scheduler."""

    @pytest.fixture
    def scheduler(self) -> Scheduler:
        """Creates a Scheduler instance with mocked dependencies."""
        scrapper_client = AsyncMock()
        telegram_client = AsyncMock()
        chat_repository = MagicMock()
        return Scheduler(scrapper_client, telegram_client, chat_repository)

    def test_extract_github_repo(self, scheduler: Scheduler) -> None:
        """Checks correct extraction of repository name from GitHub URL."""
        github_url = "https://github.com/owner/repo"
        repo_name = scheduler.extract_github_repo(github_url)
        assert repo_name == "owner/repo"

        github_url_with_path = "https://github.com/owner/repo/issues/123"
        repo_name = scheduler.extract_github_repo(github_url_with_path)
        assert repo_name == "owner/repo"

        invalid_url = "https://example.com"
        repo_name = scheduler.extract_github_repo(invalid_url)
        assert repo_name == ""

    def test_extract_stackoverflow_question_id(self, scheduler: Scheduler) -> None:
        """Checks correct extraction of question ID from StackOverflow URL."""
        stackoverflow_url = "https://stackoverflow.com/questions/12345/example-question"
        question_id = scheduler.extract_stackoverflow_question_id(stackoverflow_url)
        correct_question_id = 12345

        assert question_id == correct_question_id

        stackoverflow_url_with_params = (
            "https://stackoverflow.com/questions/12345/example-question?answertab=votes"
        )
        question_id = scheduler.extract_stackoverflow_question_id(stackoverflow_url_with_params)
        assert question_id == correct_question_id

        invalid_url = "https://example.com"
        question_id = scheduler.extract_stackoverflow_question_id(invalid_url)
        correct_question_id = 0
        assert question_id == correct_question_id
