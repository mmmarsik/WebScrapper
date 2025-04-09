import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class BaseClient(ABC):
    """Base class for API clients."""

    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        """Initialize the client.

        Args:
            base_url: The base URL for API requests.
            timeout: The timeout for API requests in seconds.

        """
        self.base_url = base_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create an HTTP client.

        Returns:
            An AsyncClient instance.

        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    @abstractmethod
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        **kwargs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Make an HTTP request to the API.

        Args:
            method: The HTTP method to use.
            endpoint: The API endpoint to request.
            params: Query parameters for the request.
            headers: headers for the request.
            **kwargs: Additional arguments to pass to the request.

        Returns:
            The JSON response from the API.

        Raises:
            httpx.HTTPError: If the request fails.

        """
        client = await self._get_client()
        url = f"{self.base_url}{endpoint}"
        request_kwargs: Dict[str, Any] = {}

        if params:
            request_kwargs["params"] = params
        if headers:
            request_kwargs["headers"] = headers
        request_kwargs.update(kwargs)

        try:
            response = await client.request(method, url, **request_kwargs)
            response.raise_for_status()
            return response.json() if response else {}
        except httpx.HTTPError:
            logger.exception("HTTP error")
            raise
        except Exception:
            logger.exception("Error making request to %s ", url)
            raise
