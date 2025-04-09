import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.scrapper.clients.base_client import BaseClient

logger = logging.getLogger(__name__)


class StackOverflowClient(BaseClient):
    """Client for interacting with the Stack Overflow API."""

    def __init__(self, timeout: float = 10.0) -> None:
        """Initialize the Stack Overflow client.

        Args:
            timeout: The timeout for API requests in seconds.

        """
        super().__init__("https://api.stackexchange.com/2.3", timeout)
        self.api_params = {
            "site": "stackoverflow",
            "key": "",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        **kwargs: Dict[str, Any],
    ) -> Dict[str, Any]:
        return await super()._make_request(method, endpoint, params, headers, **kwargs)

    async def get_question_info(self, question_id: int) -> Dict[str, Any]:
        """Get information about a Stack Overflow question.

        Args:
            question_id: The ID of the question.

        Returns:
            Question information.

        """
        endpoint = f"/questions/{question_id}"
        params = {
            **self.api_params,
            "filter": "withbody",
        }

        response = await self._make_request("GET", endpoint, params=params)

        if response.get("items") and len(response["items"]) > 0:
            return response["items"][0] if response["items"] else {}
        return {}

    async def get_question_last_activity(self, question_id: int) -> datetime:
        """Get the last activity time of a Stack Overflow question.

        Args:
            question_id: The ID of the question.

        Returns:
            The last activity time.

        """
        question_info = await self.get_question_info(question_id)
        last_activity_date = question_info.get("last_activity_date")

        if last_activity_date:
            return datetime.fromtimestamp(last_activity_date, tz=timezone.utc)
        return datetime.min.replace(tzinfo=timezone.utc)

    async def get_recent_answers(self, question_id: int, since: datetime) -> List[Dict[str, Any]]:
        """Get answers to a question created since a specific time.

        Args:
            question_id: The ID of the question.
            since: The time to check from.

        Returns:
            A list of answers.

        """
        endpoint = f"/questions/{question_id}/answers"
        params = {
            **self.api_params,
            "filter": "withbody",
            "sort": "creation",
            "order": "desc",
        }

        response = await self._make_request("GET", endpoint, params=params)

        recent_answers = []
        for answer in response.get("items", []):
            creation_date = datetime.fromtimestamp(answer["creation_date"], tz=timezone.utc)
            if creation_date > since:
                body_markdown = answer.get("body_markdown", answer.get("body", ""))

                recent_answers.append(
                    {
                        "owner": answer.get("owner", {}),
                        "creation_date": answer["creation_date"],
                        "body_markdown": body_markdown,
                        "score": answer.get("score", 0),
                        "is_accepted": answer.get("is_accepted", False),
                        "link": answer.get("link", ""),
                    },
                )

        return recent_answers

    async def get_recent_comments(self, question_id: int, since: datetime) -> List[Dict[str, Any]]:
        """Get comments on a question created since a specific time.

        Args:
            question_id: The ID of the question.
            since: The time to check from.

        Returns:
            A list of comments.

        """
        endpoint = f"/questions/{question_id}/comments"
        params = {
            **self.api_params,
            "filter": "withbody",
            "sort": "creation",
            "order": "desc",
        }

        response = await self._make_request("GET", endpoint, params=params)

        recent_comments = []
        for comment in response.get("items", []):
            creation_date = datetime.fromtimestamp(comment["creation_date"], tz=timezone.utc)
            if creation_date > since:
                body_markdown = comment.get("body_markdown", comment.get("body", ""))

                recent_comments.append(
                    {
                        "owner": comment.get("owner", {}),
                        "creation_date": comment["creation_date"],
                        "body_markdown": body_markdown,
                        "score": comment.get("score", 0),
                        "link": comment.get("link", ""),
                    },
                )

        return recent_comments
