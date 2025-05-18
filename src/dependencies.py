"""This module provides dependency injection functions for accessing database
repositories and sessions. It supplies functions to retrieve the appropriate
chat and link repository instances based on the repository access type
defined in the application's settings, as well as an asynchronous SQLAlchemy
session for database operations.

Available repository implementations:
    - ORM-based repositories.
    - SQL-based repositories.

These dependencies are intended for use with FastAPI's dependency injection system.
"""

from fastapi import Request

from src.bot.notification_sender.http_sender import HttpSender
from src.db.repositories.base import (
    ChatRepositoryInterface,
    LinkRepositoryInterface,
    TagRepositoryInterface,
)
from src.db.repositories.orm_repository.chat_repository import ORMChatRepository
from src.db.repositories.orm_repository.link_repository import ORMLinkRepository
from src.db.repositories.orm_repository.tag_repository import ORMTagRepository
from src.db.repositories.sql_repository.chat_repository import SQLChatRepository
from src.db.repositories.sql_repository.link_repository import SQLLinkRepository
from src.db.repositories.sql_repository.tag_repository import SQLTagRepository
from src.db.repositories.types import RepositoryAccessType


def get_chat_repo(request: Request) -> ChatRepositoryInterface:
    """Dependency function to obtain a chat repository instance.

    This function selects the appropriate chat repository implementation (ORM or SQL)

    Args:
        request (Request): The FastAPI request object, which contains the application state.

    Returns:
        ChatRepositoryInterface: An instance of the appropriate chat repository.

    Raises:
        ValueError: If the repository access type is not supported.

    """
    access_type: RepositoryAccessType = request.app.state.db_settings.access_type
    if access_type == RepositoryAccessType.ORM:
        return ORMChatRepository(request.app.state.async_session_maker)
    elif access_type == RepositoryAccessType.SQL:
        return SQLChatRepository(request.app.state.sql_connection_pool)
    else:
        raise ValueError(f"Unsupported repository access type: {access_type}")


def get_link_repo(request: Request) -> LinkRepositoryInterface:
    """Dependency function to obtain a link repository instance.

    This function selects the appropriate link repository implementation (ORM or SQL)

    Args:
        request (Request): The FastAPI request object, which contains the application state.

    Returns:
        LinkRepositoryInterface: An instance of the appropriate link repository.

    Raises:
        ValueError: If the repository access type is not supported.

    """
    access_type: RepositoryAccessType = request.app.state.db_settings.access_type
    if access_type == RepositoryAccessType.ORM:
        return ORMLinkRepository(request.app.state.async_session_maker)
    elif access_type == RepositoryAccessType.SQL:
        return SQLLinkRepository(request.app.state.sql_connection_pool)
    else:
        raise ValueError(f"Unsupported repository access type: {access_type}")


def get_tag_repo(request: Request) -> TagRepositoryInterface:
    """Dependency function to obtain a tag repository instance.

    This function selects the appropriate tag repository implementation (ORM or SQL)

    Args:
       request (Request): The FastAPI request object, which contains the application state.

    Returns:
        TagRepositoryInterface: An instance of the appropriate tag repository.

    Raises:
        ValueError: If the repository access type is not supported.

    """
    access_type: RepositoryAccessType = request.app.state.db_settings.access_type
    match access_type:
        case RepositoryAccessType.ORM:
            return ORMTagRepository(request.app.state.async_session_maker)
        case RepositoryAccessType.SQL:
            return SQLTagRepository(request.app.state.sql_connection_pool)
        case _:
            raise ValueError(f"Unsupported repository access type: {access_type}")


def get_http_sender(request: Request) -> HttpSender:
    """Dependency function to obtain an HTTP sender instance.

    Args:
       request (Request): The FastAPI request object, which contains the application state.

    Returns:
        HttpSender: An instance of the HTTP sender.

    """
    http_sender: HttpSender = request.app.state.notification_sender
    return http_sender
