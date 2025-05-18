import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Tuple

from telethon import TelegramClient

from src.bot.notification_sender.base import SenderInterface
from src.db.repositories.base import ChatRepositoryInterface, LinkAddError, LinkRepositoryInterface
from src.scrapper.client import ScrapperAPIClient
from src.scrapper.clients.clients_exceptions.github_exceptions import (
    GitHubClientError,
    GitHubRepoNotFoundError,
)
from src.scrapper.clients.clients_exceptions.stackoverflow_exceptions import (
    StackOverflowClientError,
    StackOverflowQuestionNotFoundError,
)
from src.scrapper.clients.github_client import GitHubClient
from src.scrapper.clients.stackoverflow_client import StackOverflowClient
from src.scrapper.models_dto import LinkDTO

logger = logging.getLogger(__name__)


class Scheduler:
    """A scheduler that periodically checks tracked links and sends notifications \
        if changes are detected.

    Features:
        - Batch processing of chat IDs.
        - Asynchronous processing of links.
        - Separate notification sending logic.
    """

    def __init__(
        self,
        scrapper_client: ScrapperAPIClient,
        telegram_client: TelegramClient,
        chat_repository: ChatRepositoryInterface,
        link_repository: LinkRepositoryInterface,
        notification_sender: SenderInterface,
        check_interval: float = 60,
        batch_size: int = 100,
    ) -> None:
        """Initializes the Scheduler.

        Args:
            scrapper_client: The client for interacting with the scraper API.
            telegram_client: The client for sending Telegram notifications.
            chat_repository: The repository for managing chat data.
            link_repository: The repository for managing link data.
            notification_sender: The service for sending notifications.
            check_interval: The interval (in seconds) at which to check for updates. Defaults to 60.
            batch_size: The number of chat IDs to process in each batch. Defaults to 100.

        """
        self.scrapper_client = scrapper_client
        self.telegram_client = telegram_client
        self.chat_repository = chat_repository
        self.link_repository = link_repository
        self.notification_sender = notification_sender
        self.check_interval = check_interval
        self.batch_size = batch_size
        self.last_updates: Dict[Tuple[int, str], datetime] = {}
        self.github_client = GitHubClient()
        self.stackoverflow_client = StackOverflowClient()
        self._running = True
        self.preview_symbols_count = 90

    async def start(self) -> None:
        """Starts the scheduler."""
        logger.info("Starting scheduler with check interval %s seconds", self.check_interval)
        while self._running:
            try:
                await self._process_chats_in_batches()
            except Exception:
                logger.exception("Error in scheduler")

            logger.debug("Waiting %s seconds until next check", self.check_interval)
            await asyncio.sleep(self.check_interval)

    async def stop(self) -> None:
        """Stops the scheduler."""
        logger.info("Stopping scheduler")
        self._running = False
        await self.github_client.close()
        await self.stackoverflow_client.close()

    async def _process_chats_in_batches(self) -> None:
        """Processes all chats in batches."""
        logger.info("Starting to process chats in batches")

        async for chat_ids_batch in self.chat_repository.get_all_chats_ids(self.batch_size):
            logger.debug("Processing batch of %d chats", len(chat_ids_batch))

            tasks = [self._process_chat(chat_id) for chat_id in chat_ids_batch]

            await asyncio.gather(*tasks)

    async def _process_chat(self, chat_id: int) -> None:
        """Processes a single chat.

        Args:
            chat_id: The ID of the chat to process.

        """
        try:
            logger.debug("Processing chat %d", chat_id)
            links = await self.link_repository.list_links(chat_id)
            if not links:
                logger.debug("No links found for chat %d", chat_id)
                return

            tasks = [self._process_link(chat_id, link) for link in links]
            results = await asyncio.gather(*tasks)

            notifications: List[Dict[str, Any]] = []
            for link, updates in zip(links, results):
                if updates:
                    logger.info(
                        "Found updates for link",
                        extra={"chat_id": chat_id, "link": link.url},
                    )
                    notifications.append(
                        {
                            "chat_id": chat_id,
                            "link": link.url,
                            "updates": updates,
                        },
                    )

            if notifications:
                logger.info("Sending %d notifications for chat %d", len(notifications), chat_id)
                await self.notification_sender.send_batch_notifications(notifications)
        except Exception:
            logger.exception("Error processing chat %d", chat_id)

    def _get_update_handler(
        self,
        url: str,
    ) -> Callable[[str, datetime], Awaitable[Dict[str, Any]]] | None:
        """Returns the update handler function for the given URL or None \
            if the type is not supported.

        Args:
            url: The URL to check.

        Returns:
            The update handler function or None.

        """
        if "github.com" in url:
            return self._check_github_update
        elif "stackoverflow.com/questions" in url:
            return self._check_stackoverflow_update
        else:
            return None

    async def _process_link(self, chat_id: int, link: LinkDTO) -> Dict[str, Any]:
        """Processes a single link for updates.

        Args:
            chat_id: The ID of the chat the link belongs to.
            link: The link to process.

        Returns:
            A dictionary of updates, or an empty dictionary if there are no updates.

        """
        try:
            if link.muted:
                logger.debug("Skipping muted link %s for chat %s", link.url, chat_id)
                return {}

            url = link.url
            logger.debug("Checking link for updates: %s", url)
            key = (chat_id, url)
            last_check_time = self.last_updates.get(key, datetime(2000, 1, 1, tzinfo=timezone.utc))

            update_handler = self._get_update_handler(url)
            if update_handler is None:
                logger.warning("Unsupported link type: %s", url)
                return {}

            updates: Dict[str, Any] = await update_handler(url, last_check_time)
            if updates:
                current_time = datetime.now(timezone.utc)
                self.last_updates[key] = current_time
                logger.info("Found updates for link", extra={"chat_id": chat_id, "link": url})
                return updates

        except StackOverflowQuestionNotFoundError:
            logger.warning("StackOverflow question not found for link %s", url)
            return {}
        except LinkAddError:
            logger.exception("Error processing link %s", url)
            return {}
        except (GitHubClientError, StackOverflowClientError):
            logger.exception("Client error checking link %s", url)
            return {}
        except Exception:
            logger.exception("Unexpected error checking link %s", url)
            return {}

        return {}

    async def _check_github_update(self, url: str, last_check_time: datetime) -> Dict[str, Any]:
        """Checks for updates on a GitHub repository.

        Args:
            url: The GitHub repository URL.
            last_check_time: The time of the last check.

        Returns:
            A dictionary of updates, or an empty dictionary if there are no updates.

        """
        repo_path = self.extract_github_repo(url)
        if not repo_path:
            logger.warning("Failed to extract repository path from GitHub URL: %s", url)
            return {}
        try:
            await self.github_client.get_repo_info(repo_path)

            recent_prs = await self.github_client.get_recent_pull_requests(
                repo_path,
                last_check_time,
            )

            recent_issues = await self.github_client.get_recent_issues(repo_path, last_check_time)

            if not recent_prs and not recent_issues:
                return {}

            updates: Dict[str, Any] = {
                "type": "github",
                "repo_name": repo_path,
                "repo_url": url,
                "pull_requests": [],
                "issues": [],
            }

            for pr in recent_prs:
                pr_info = {
                    "title": pr["title"],
                    "user": pr["user"],
                    "created_at": pr["created_at"],
                    "description": (
                        pr["description"][: self.preview_symbols_count] + "..."
                        if len(pr["description"]) > self.preview_symbols_count
                        else pr["description"]
                    ),
                    "url": pr["url"],
                    "number": pr["number"],
                    "state": pr["state"],
                }
                updates["pull_requests"].append(pr_info)

            for issue in recent_issues:
                issue_info = {
                    "title": issue["title"],
                    "user": issue["user"],
                    "created_at": issue["created_at"],
                    "description": (
                        issue["description"][: self.preview_symbols_count] + "..."
                        if len(issue["description"]) > self.preview_symbols_count
                        else issue["description"]
                    ),
                    "url": issue["url"],
                    "number": issue["number"],
                    "state": issue["state"],
                }
                updates["issues"].append(issue_info)

        except GitHubRepoNotFoundError:
            logger.warning("GitHub repository not found: %s", url)
            return {}
        except GitHubClientError:
            logger.exception("Error checking GitHub updates for %s", url)
            return {}
        except Exception:
            logger.exception("Unexpected error checking GitHub updates for %s", url)
            return {}

        return updates

    async def _check_stackoverflow_update(
        self,
        url: str,
        last_check_time: datetime,
    ) -> Dict[str, Any]:
        """Checks for updates on a StackOverflow question.

        Args:
            url: The StackOverflow question URL.
            last_check_time: The time of the last check.

        Returns:
            A dictionary of updates, or an empty dictionary if there are no updates.

        """
        question_id = self.extract_stackoverflow_question_id(url)
        if not question_id:
            logger.warning("Failed to extract question ID from StackOverflow URL: %s", url)
            return {}
        try:
            question_info = await self.stackoverflow_client.get_question_info(question_id)

            new_answers = await self.stackoverflow_client.get_recent_answers(
                question_id,
                last_check_time,
            )

            new_comments = await self.stackoverflow_client.get_recent_comments(
                question_id,
                last_check_time,
            )

            if not new_answers and not new_comments:
                return {}

            updates = {
                "type": "stackoverflow",
                "question_id": question_id,
                "question_title": question_info.get("title", ""),
                "question_url": url,
                "answers": [],
                "comments": [],
            }

            for answer in new_answers:
                answer_info = {
                    "user": answer.get("owner", {}).get("display_name", "Unknown"),
                    "created_at": answer.get("creation_date", ""),
                    "text": (
                        answer.get("body_markdown", "")[: self.preview_symbols_count] + "..."
                        if len(answer.get("body_markdown", "")) > self.preview_symbols_count
                        else answer.get("body_markdown", "")
                    ),
                    "score": answer.get("score", 0),
                    "is_accepted": answer.get("is_accepted", False),
                }
                updates["answers"].append(answer_info)

            for comment in new_comments:
                comment_info = {
                    "user": comment.get("owner", {}).get("display_name", "Unknown"),
                    "created_at": comment.get("creation_date", ""),
                    "text": (
                        comment.get("body_markdown", "")[: self.preview_symbols_count] + "..."
                        if len(comment.get("body_markdown", "")) > self.preview_symbols_count
                        else comment.get("body_markdown", "")
                    ),
                    "score": comment.get("score", 0),
                }
                updates["comments"].append(comment_info)

        except StackOverflowQuestionNotFoundError:
            logger.warning("StackOverflow question not found: %s", url)
            return {}
        except StackOverflowClientError:
            logger.exception("Error checking StackOverflow updates for %s", url)
            return {}
        except Exception:
            logger.exception("Unexpected error checking StackOverflow updates for %s", url)
            return {}

        return updates

    def extract_github_repo(self, url: str) -> str:
        """Extracts the GitHub repository name in the format "owner/repo" from a URL.

        Args:
            url: The GitHub repository URL.

        Returns:
            The repository name in "owner/repo" format, or an empty string if extraction fails.

        """
        try:
            parts = url.split("/")
            owner = parts[3]
            repo = parts[4].split("#")[0].split("?")[0]
        except Exception:
            logger.exception("Error extracting GitHub repo from URL %s", url)
            return ""
        return f"{owner}/{repo}"

    def extract_stackoverflow_question_id(self, url: str) -> int:
        """Extracts the question ID from a StackOverflow URL.

        Args:
            url: The StackOverflow question URL.

        Returns:
            The question ID, or 0 if extraction fails.

        """
        try:
            parts = url.split("/")
            return int(parts[4])
        except Exception:
            logger.exception("Error extracting StackOverflow question ID from URL %s", url)
            return 0
