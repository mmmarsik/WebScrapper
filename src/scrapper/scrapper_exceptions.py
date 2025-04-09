class ScrapperAPIError(Exception):
    """Base exception for Scrapper API errors."""


class ScrapperAPIHTTPError(ScrapperAPIError):
    """Raised for HTTP errors (4xx or 5xx responses)."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class ScrapperAPIRequestError(ScrapperAPIError):
    """Raised for request errors (e.g., network issues)."""
