import logging
from typing import Any, Dict, List

from telethon import TelegramClient

from src.bot.notification_sender.base import SenderInterface

logger = logging.getLogger(__name__)


class HttpSender(SenderInterface):
    """HTTP implementation of the notification sender interface."""

    def __init__(self, telegram_client: TelegramClient) -> None:
        """Initializes HttpSender with the provided TelegramClient instance.

        Args:
            telegram_client: An instance of TelegramClient for sending messages.

        """
        self.telegram_client = telegram_client
        logger.info("Initialized HttpSender with provided Telegram client.")

    async def send_notification(self, chat_id: int, link: str, updates: Dict[str, Any]) -> bool:
        """Sends a notification about a link update directly to Telegram.

        Args:
            chat_id: The ID of the chat to send the notification to.
            link: The URL of the tracked link.
            updates: A dictionary containing the update information.

        Returns:
            True if the notification was sent successfully, False otherwise.

        """
        message = f"Update for link:\n{link}\n\n{self.format_update_description(updates)}"
        try:
            logger.debug(
                "Sending notification to Telegram",
                extra={"chat_id": chat_id, "link": link},
            )
            await self.telegram_client.send_message(entity=chat_id, message=message)
            logger.info(
                "Successfully sent notification to Telegram",
                extra={"chat_id": chat_id, "link": link},
            )
        except Exception as e:
            logger.exception(
                "Error sending notification via Telegram",
                extra={"chat_id": chat_id, "link": link, "error": str(e)},
            )
            return False

        return True

    async def send_batch_notifications(
        self,
        notifications: List[Dict[str, Any]],
    ) -> Dict[int, bool]:
        """Sends multiple notifications in a batch.

        Args:
            notifications: A list of dictionaries, each containing:
                - chat_id: The ID of the chat.
                - link: The URL of the link.
                - updates: A dictionary with update data.

        Returns:
            A dictionary mapping chat_id to the notification sending status.

        """
        results = {}
        for notification in notifications:
            chat_id = notification.get("chat_id")
            link = notification.get("link")
            updates = notification.get("updates")
            if chat_id is None or link is None or updates is None:
                logger.warning("Invalid notification format", extra={"notification": notification})
                continue
            success = await self.send_notification(chat_id, link, updates)
            results[chat_id] = success
        return results

    def format_update_description(self, updates: Dict[str, Any]) -> str:
        """Formats the update description into a human-readable string.

        Args:
            updates: A dictionary containing the update information.

        Returns:
            A formatted string describing the update.

        """
        update_type = updates.get("type")
        if update_type == "github":
            return self._format_github_update(updates)
        elif update_type == "stackoverflow":
            return self._format_stackoverflow_update(updates)
        else:
            return "Updates for the link."

    def _format_github_update(self, updates: Dict[str, Any]) -> str:
        """Formats a GitHub update into a human-readable string.

        Args:
            updates: A dictionary containing the GitHub update information.

        Returns:
            A formatted string describing the GitHub update.

        """
        repo_name = updates.get("repo_name", "unknown repository")
        prs = updates.get("pull_requests", [])
        issues = updates.get("issues", [])
        lines = [f"📢 Updates in the repository {repo_name}:"]
        if prs:
            lines.append("\n🔄 New Pull Requests:")
            for pr in prs:
                title = pr.get("title", "")
                user = pr.get("user", "")
                created_at = pr.get("created_at", "")
                description = pr.get("description", "")
                url = pr.get("url", "")
                lines.append(f"- {title}")
                lines.append(f"  Author: {user}, Created: {created_at}")
                lines.append(f"  {description}")
                lines.append(f"  Link: {url}")
                lines.append("")
        if issues:
            lines.append("\n🐛 New Issues:")
            for issue in issues:
                title = issue.get("title", "")
                user = issue.get("user", "")
                created_at = issue.get("created_at", "")
                description = issue.get("description", "")
                url = issue.get("url", "")
                lines.append(f"- {title}")
                lines.append(f"  Author: {user}, Created: {created_at}")
                lines.append(f"  {description}")
                lines.append(f"  Link: {url}")
                lines.append("")
        return "\n".join(lines)

    def _format_stackoverflow_update(self, updates: Dict[str, Any]) -> str:
        """Formats a Stack Overflow update into a human-readable string.

        Args:
            updates: A dictionary containing the Stack Overflow update information.

        Returns:
            A formatted string describing the Stack Overflow update.

        """
        lines = ["Stack Overflow Updates:"]
        question_title = updates.get("question_title", "Question without title")
        question_url = updates.get("question_url", "")
        lines.append(f"Question: {question_title}")
        lines.append(f"Link: {question_url}")
        answers = updates.get("answers", [])
        comments = updates.get("comments", [])
        if answers:
            lines.append("\n✅ New Answers:")
            for answer in answers:
                user = answer.get("user", "")
                created_at = answer.get("created_at", "")
                text = answer.get("text", "")
                score = answer.get("score", 0)
                accepted_mark = "✓" if answer.get("is_accepted", False) else ""
                lines.append(
                    f"- Answer from {user} {accepted_mark}, Score: {score}, Created: {created_at}",
                )
                lines.append(f"  {text}")
                lines.append("")
        if comments:
            lines.append("\n💬 New Comments:")
            for comment in comments:
                user = comment.get("user", "")
                created_at = comment.get("created_at", "")
                text = comment.get("text", "")
                score = comment.get("score", 0)
                lines.append(f"- Comment from {user}, Score: {score}, Created: {created_at}")
                lines.append(f"  {text}")
                lines.append("")
        return "\n".join(lines)
