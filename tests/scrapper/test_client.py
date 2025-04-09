import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.scrapper.client import ScrapperAPIClient


@pytest.mark.asyncio
async def test_scrapper_client_add_link() -> None:
    """Test that ScrapperAPIClient correctly sends add_link requests.

    Verifies that the client sends proper HTTP requests with correct parameters.
    """
    base_url = "https://example.com"
    chat_id = 12345
    url = "https://github.com/user/repo"
    tags = ["test", "github"]
    filters = ["python"]

    # Create a proper mock response with request attribute
    mock_request = httpx.Request("POST", f"{base_url}/links")
    mock_response = httpx.Response(
        status_code=200,
        json={"status": "success"},
        request=mock_request,
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        client = ScrapperAPIClient(base_url=base_url)
        result = await client.add_link(chat_id, url, tags, filters)

        mock_post.assert_called_once()

        # Verify URL was correctly formed
        request_url = str(mock_post.call_args[0][0])
        assert f"{base_url}/links" in request_url

        # Verify payload was correctly sent
        payload = mock_post.call_args[1]["json"]
        assert payload["link"] == url
        assert sorted(payload["tags"]) == sorted(tags)
        assert sorted(payload["filters"]) == sorted(filters)

        # Verify headers contain chat ID
        headers = mock_post.call_args[1]["headers"]
        assert headers["Tg-Chat-Id"] == str(chat_id)

        # Verify response is returned
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_scrapper_client_remove_link() -> None:
    """Test that ScrapperAPIClient correctly sends remove_link requests.

    Verifies that the client sends proper HTTP requests with correct parameters.
    """
    base_url = "https://example.com"
    chat_id = 12345
    url = "https://github.com/user/repo"

    # Create a proper mock response with request attribute
    mock_request = httpx.Request("DELETE", f"{base_url}/links")
    mock_response = httpx.Response(
        status_code=200,
        json={"status": "success"},
        request=mock_request,
    )

    with patch("httpx.AsyncClient.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_response

        client = ScrapperAPIClient(base_url=base_url)
        result = await client.remove_link(chat_id, url)

        mock_send.assert_called_once()

        # Verify request was properly formed
        request = mock_send.call_args[0][0]
        assert request.method == "DELETE"
        assert f"{base_url}/links" in str(request.url)

        # Verify headers
        assert request.headers["Tg-Chat-Id"] == str(chat_id)
        assert "application/json" in request.headers["Content-Type"]

        # Verify content
        content = json.loads(request.content)
        assert content["link"] == url

        # Verify response is returned
        assert result["status"] == "success"


@pytest.mark.asyncio
async def test_scrapper_client_list_links() -> None:
    """Test that ScrapperAPIClient correctly sends list_links requests.

    Verifies that the client sends proper HTTP requests and processes responses.
    """
    base_url = "https://example.com"
    chat_id = 12345

    # Create a proper mock response with request attribute
    mock_request = httpx.Request("GET", f"{base_url}/links")
    mock_response = httpx.Response(
        status_code=200,
        json={
            "links": [
                {"url": "https://github.com/user/repo", "tags": ["test"], "filters": ["python"]},
                {"url": "https://stackoverflow.com/q/12345", "tags": ["qa"], "filters": []},
            ],
        },
        request=mock_request,
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        client = ScrapperAPIClient(base_url=base_url)
        result = await client.list_links(chat_id)

        mock_get.assert_called_once()

        # Verify URL and parameters
        request_url = str(mock_get.call_args[0][0])
        assert f"{base_url}/links" in request_url

        # Verify headers contain chat ID
        headers = mock_get.call_args[1]["headers"]
        assert headers["Tg-Chat-Id"] == str(chat_id)

        # Verify response content

        correct_message_parts_count = 2
        assert len(result["links"]) == correct_message_parts_count
        assert result["links"][0]["url"] == "https://github.com/user/repo"
        assert result["links"][1]["url"] == "https://stackoverflow.com/q/12345"
