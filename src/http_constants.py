from enum import Enum


class HTTPStatus(Enum):
    """HTTP status codes."""

    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500
    NOT_FOUND = 404
    OK = 200
    UNAUTHORIZED = 401
