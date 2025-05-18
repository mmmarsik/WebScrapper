import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

import httpx

logger = logging.getLogger(__name__)


@dataclass
class RequestParams:
    method: str
    endpoint: str
    params: Optional[Dict[str, Any]] = field(default_factory=dict)
    headers: Optional[Dict[str, Any]] = field(default_factory=dict)
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = field(default=None)
    kwargs: Dict[str, Any] = field(default_factory=dict)


class BaseClient:
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

    async def _make_request(self, request_params: RequestParams) -> Dict[str, Any]:
        """Make an HTTP request to the API.

        Args:
            request_params: An instance of RequestParams containing all request parameters.

        Returns:
            The JSON response from the API.

        Raises:
            httpx.HTTPError: If the request fails.

        """
        client = await self._get_client()
        url = f"{self.base_url}{request_params.endpoint}"
        request_kwargs: Dict[str, Any] = {}

        if request_params.params:
            request_kwargs["params"] = request_params.params
        if request_params.headers:
            request_kwargs["headers"] = request_params.headers
        if request_params.data:
            request_kwargs["json"] = request_params.data
        request_kwargs.update(request_params.kwargs)

        try:
            response = await client.request(request_params.method, url, **request_kwargs)
            response.raise_for_status()
            return response.json() if response else {}
        except httpx.HTTPError:
            logger.exception("HTTP error during request")
            raise
        except Exception:
            logger.exception("Error making request to %s ", url)
            raise
