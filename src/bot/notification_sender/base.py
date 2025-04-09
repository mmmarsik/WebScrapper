from abc import ABC, abstractmethod
from typing import Any, Dict, List


class SenderInterface(ABC):
    """Interface for notification senders.

    This interface defines methods for sending notifications about updates
    to tracked links.
    """

    @abstractmethod
    async def send_notification(self, chat_id: int, link: str, updates: Dict[str, Any]) -> bool:
        """Sends a notification about updates to a tracked link.

        Args:
            chat_id: The ID of the chat to send the notification to.
            link: The URL of the tracked link that has updates.
            updates: A dictionary containing update information.

        Returns:
            bool: True if the notification was sent successfully, False otherwise.

        """

    @abstractmethod
    async def send_batch_notifications(
        self,
        notifications: List[Dict[str, Any]],
    ) -> Dict[int, bool]:
        """Sends multiple notifications in a batch.

        Args:
            notifications: A list of dictionaries, each containing:
                - chat_id: The ID of the chat to send the notification to.
                - link: The URL of the tracked link that has updates.
                - updates: A dictionary containing update information.

        Returns:
            Dict[int, bool]: A dictionary mapping chat IDs to success status.

        """

    @abstractmethod
    def format_update_description(self, updates: Dict[str, Any]) -> str:
        """Formats the update description into a human-readable string.

        Args:
            updates: A dictionary containing the update information.

        Returns:
            A formatted string describing the update.

        """
