import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, cast

from src.scrapper.clients.base_client import BaseClient

logger = logging.getLogger(__name__)


class GitHubClient(BaseClient):
    """Client for interacting with the GitHub API."""

    def __init__(self, timeout: float = 10.0) -> None:
        """Initialize the GitHub client.

        Args:
            timeout: The timeout for API requests in seconds.

        """
        super().__init__("https://api.github.com", timeout)
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
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

    async def get_repo_info(self, repo_path: str) -> Dict[str, Any]:
        """Get information about a GitHub repository.

        Args:
            repo_path: The repository path in the format "owner/repo".

        Returns:
            Repository information.

        """
        endpoint = f"/repos/{repo_path}"
        return await self._make_request("GET", endpoint, headers=self.headers)

    async def get_repo_last_updated(self, repo_path: str) -> datetime:
        """Get the last update time of a GitHub repository.

        Args:
            repo_path: The repository path in the format "owner/repo".

        Returns:
            The last update time.

        """
        repo_info = await self.get_repo_info(repo_path)
        updated_at = repo_info.get("updated_at")
        if updated_at:
            return datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        return datetime.min.replace(tzinfo=timezone.utc)

    async def get_recent_pull_requests(
        self,
        repo_path: str,
        since: datetime,
    ) -> List[Dict[str, Any]]:
        """Get pull requests created or updated since a specific time.

        Args:
            repo_path: The repository path in the format "owner/repo".
            since: The time to check from.

        Returns:
            A list of pull requests.

        """
        endpoint = f"/repos/{repo_path}/pulls"
        params = {
            "state": "all",
            "sort": "updated",
            "direction": "desc",
            "per_page": 100,
        }

        result = await self._make_request("GET", endpoint, params=params, headers=self.headers)
        all_prs = cast(List[Dict[str, Any]], result)

        recent_prs = []
        for pr in all_prs:
            if not isinstance(pr, dict):
                continue

            updated_at_str = pr.get("updated_at", "")
            if not updated_at_str or not isinstance(updated_at_str, str):
                continue

            updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
            if updated_at > since:
                recent_prs.append(
                    {
                        "title": pr.get("title", ""),
                        "user": (
                            pr.get("user", {}).get("login", "")
                            if isinstance(pr.get("user"), dict)
                            else ""
                        ),
                        "created_at": pr.get("created_at", ""),
                        "updated_at": pr.get("updated_at", ""),
                        "description": pr.get("body", "") or "",
                        "url": pr.get("html_url", ""),
                        "number": pr.get("number", 0),
                        "state": pr.get("state", ""),
                    },
                )
            else:
                break

        return recent_prs

    async def get_recent_issues(self, repo_path: str, since: datetime) -> List[Dict[str, Any]]:
        """Get issues created or updated since a specific time.

        Args:
            repo_path: The repository path in the format "owner/repo".
            since: The time to check from.

        Returns:
            A list of issues.

        """
        endpoint = f"/repos/{repo_path}/issues"
        params = {
            "state": "all",
            "sort": "updated",
            "direction": "desc",
            "per_page": 100,
            "filter": "all",
        }

        result = await self._make_request("GET", endpoint, params=params, headers=self.headers)
        all_issues = cast(List[Dict[str, Any]], result)

        recent_issues = []
        for issue in all_issues:
            if not isinstance(issue, dict):
                continue

            if issue.get("pull_request") is not None:
                continue

            updated_at_str = issue.get("updated_at", "")
            if not updated_at_str or not isinstance(updated_at_str, str):
                continue

            updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
            if updated_at > since:
                recent_issues.append(
                    {
                        "title": issue.get("title", ""),
                        "user": (
                            issue.get("user", {}).get("login", "")
                            if isinstance(issue.get("user"), dict)
                            else ""
                        ),
                        "created_at": issue.get("created_at", ""),
                        "updated_at": issue.get("updated_at", ""),
                        "description": issue.get("body", "") or "",
                        "url": issue.get("html_url", ""),
                        "number": issue.get("number", 0),
                        "state": issue.get("state", ""),
                    },
                )
            else:
                break

        return recent_issues
