import json
import logging
from typing import Any, Dict, List, cast

import httpx

from src.scrapper.scrapper_exceptions import (
    ScrapperAPIError,
    ScrapperAPIHTTPError,
    ScrapperAPIRequestError,
)

logger = logging.getLogger(__name__)


class ScrapperAPIClient:
    """Client for interacting with the Scrapper API."""

    def __init__(self, base_url: str, timeout: int = 10) -> None:
        """Initialize the ScrapperAPIClient.

        Args:
            base_url (str): The base URL of the Scrapper API.
            timeout (int, optional): Timeout for HTTP requests (in seconds). Defaults to 10.

        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def register_chat(self, chat_id: int) -> Dict[str, Any]:
        """Register a Telegram chat with the Scrapper API.

        Sends a POST request to /tg-chat/{chat_id}.

        Args:
            chat_id (int): Telegram chat identifier.

        Returns:
            Dict[str, Any]: JSON response from the API.

        Raises:
            ScrapperAPIHTTPError:  If the API returns an error status code.
            ScrapperAPIRequestError: If there's a network issue.
            ScrapperAPIError: For other unexpected errors.

        """
        url = f"{self.base_url}/tg-chat/{chat_id}"
        try:
            response = await self.client.post(url)
            response.raise_for_status()
            logger.info("Chat registered", extra={"chat_id": chat_id})
            return cast(Dict[str, Any], response.json())
        except httpx.HTTPStatusError as e:
            raise ScrapperAPIHTTPError(
                f"Failed to register chat: {e}",
                e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            raise ScrapperAPIRequestError(f"Request to Scrapper API failed: {e}") from e
        except Exception as e:
            raise ScrapperAPIError(f"An unexpected error occurred: {e}") from e

    async def unregister_chat(self, chat_id: int) -> None:
        """Unregister a Telegram chat from the Scrapper API.

        Sends a DELETE request to /tg-chat/{chat_id}.

        Args:
            chat_id (int): Telegram chat identifier.

        Raises:
            ScrapperAPIHTTPError:  If the API returns an error status code.
            ScrapperAPIRequestError: If there's a network issue.
            ScrapperAPIError: For other unexpected errors.

        """
        url = f"{self.base_url}/tg-chat/{chat_id}"
        try:
            response = await self.client.delete(url)
            response.raise_for_status()
            logger.info("Chat unregistered", extra={"chat_id": chat_id})
        except httpx.HTTPStatusError as e:
            raise ScrapperAPIHTTPError(
                f"Failed to unregister chat: {e}",
                e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            raise ScrapperAPIRequestError(f"Request to Scrapper API failed: {e}") from e
        except Exception as e:
            raise ScrapperAPIError(f"An unexpected error occurred: {e}") from e

    async def add_link(
        self,
        chat_id: int,
        url: str,
        tags: List[str],
        filters: List[str],
    ) -> Dict[str, Any]:
        """Add a link to the tracking list.

        Args:
            chat_id (int): Telegram chat identifier.
            url (str): Link to be tracked.
            tags (List[str]): Tags associated with the link.
            filters (List[str]): Filters applied to the link.

        Returns:
            Dict[str, Any]: JSON response from the API.

        Raises:
            ScrapperAPIHTTPError:  If the API returns an error status code.
            ScrapperAPIRequestError: If there's a network issue.
            ScrapperAPIError: For other unexpected errors.

        """
        url_endpoint = f"{self.base_url}/links"
        payload = {"link": url, "tags": tags, "filters": filters}
        headers = {"Tg-Chat-Id": str(chat_id)}
        try:
            response = await self.client.post(url_endpoint, json=payload, headers=headers)
            response.raise_for_status()
            logger.info("Link added", extra={"chat_id": chat_id, "url": url})
            return cast(Dict[str, Any], response.json())
        except httpx.HTTPStatusError as e:
            raise ScrapperAPIHTTPError(f"Failed to add link: {e}", e.response.status_code) from e
        except httpx.RequestError as e:
            raise ScrapperAPIRequestError(f"Request to Scrapper API failed: {e}") from e

    async def remove_link(self, chat_id: int, url: str) -> Dict[str, Any]:
        """Remove a tracked link.

        Args:
            chat_id (int): Telegram chat identifier.
            url (str): Link to be removed.

        Returns:
            Dict[str, Any]: JSON response from the API.

        """
        url_endpoint = f"{self.base_url}/links"
        headers = {"Tg-Chat-Id": str(chat_id), "Content-Type": "application/json"}
        try:
            response = await self.client.send(
                httpx.Request(
                    method="DELETE",
                    url=url_endpoint,
                    headers=headers,
                    content=json.dumps({"link": url}),
                ),
            )
            response.raise_for_status()
            logger.info("Link removed", extra={"chat_id": chat_id, "url": url})
            return cast(Dict[str, Any], response.json())
        except httpx.HTTPStatusError as e:
            raise ScrapperAPIHTTPError(f"Failed to remove link: {e}", e.response.status_code) from e
        except httpx.RequestError as e:
            raise ScrapperAPIRequestError(f"Request to Scrapper API failed: {e}") from e

    async def list_links(self, chat_id: int) -> Dict[str, Any]:
        """Retrieve the list of tracked links as raw JSON.

        Args:
            chat_id (int): Telegram chat identifier.

        Returns:
            Dict[str, Any]: JSON response from the API.

        """
        url_endpoint = f"{self.base_url}/links"
        headers = {"Tg-Chat-Id": str(chat_id)}
        try:
            response = await self.client.get(url_endpoint, headers=headers)
            response.raise_for_status()
            logger.info("List of links retrieved", extra={"chat_id": chat_id})
            return cast(Dict[str, Any], response.json())
        except httpx.HTTPStatusError as e:
            raise ScrapperAPIHTTPError(f"Failed to list links: {e}", e.response.status_code) from e
        except httpx.RequestError as e:
            raise ScrapperAPIRequestError(f"Request to Scrapper API failed: {e}") from e
        except Exception as e:
            raise ScrapperAPIError(f"An unexpected error occurred: {e}") from e

    async def close(self) -> None:
        """Close the httpx client session."""
        await self.client.aclose()
        logger.info("HTTP client closed")

    async def mute_tag(self, chat_id: int, tag_name: str) -> Dict[str, Any]:
        """Mute a tag for a specific chat.

        Args:
            chat_id: The ID of the chat.
            tag_name: The name of the tag to mute.

        Returns:
            Dict[str, Any]: JSON response from the API.

        Raises:
            ScrapperAPIHTTPError: If the API returns an error status code.
            ScrapperAPIRequestError: If there's a network issue.
            ScrapperAPIError: For other unexpected errors.

        """
        url_endpoint = f"{self.base_url}/tags/mute"
        payload = {"tag_name": tag_name}
        headers = {"Tg-Chat-Id": str(chat_id)}

        try:
            response = await self.client.post(url_endpoint, json=payload, headers=headers)
            response.raise_for_status()
            logger.info("Tag muted", extra={"chat_id": chat_id, "tag": tag_name})
            return cast(Dict[str, Any], response.json())
        except httpx.HTTPStatusError as e:
            raise ScrapperAPIHTTPError(f"Failed to mute tag: {e}", e.response.status_code) from e
        except httpx.RequestError as e:
            raise ScrapperAPIRequestError(f"Request to Scrapper API failed: {e}") from e

    async def unmute_tag(self, chat_id: int, tag_name: str) -> Dict[str, Any]:
        """Unmute a tag for a specific chat.

        Args:
            chat_id: The ID of the chat.
            tag_name: The name of the tag to unmute.

        Returns:
            Dict[str, Any]: JSON response from the API.

        Raises:
            ScrapperAPIHTTPError: If the API returns an error status code.
            ScrapperAPIRequestError: If there's a network issue.
            ScrapperAPIError: For other unexpected errors.

        """
        url_endpoint = f"{self.base_url}/tags/unmute"
        payload = {"tag_name": tag_name}
        headers = {"Tg-Chat-Id": str(chat_id)}

        try:
            response = await self.client.post(url_endpoint, json=payload, headers=headers)
            response.raise_for_status()
            logger.info("Tag unmuted", extra={"chat_id": chat_id, "tag": tag_name})
            return cast(Dict[str, Any], response.json())
        except httpx.HTTPStatusError as e:
            raise ScrapperAPIHTTPError(f"Failed to unmute tag: {e}", e.response.status_code) from e
        except httpx.RequestError as e:
            raise ScrapperAPIRequestError(f"Request to Scrapper API failed: {e}") from e
