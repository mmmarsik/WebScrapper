import logging
from typing import AsyncGenerator, List, Optional, cast

from src.db.repositories.base import ChatRepositoryInterface
from src.db.repositories.sql_repository.sql_pool_manager import SQLConnectionPool
from src.scrapper.models_dto import UserDTO

logger = logging.getLogger(__name__)


class SQLChatRepository(ChatRepositoryInterface):
    """SQL implementation of the chat repository interface."""

    def __init__(self, connection: SQLConnectionPool) -> None:
        """Initialize the SQL chat repository.

        Args:
            connection: The SQL connection.

        """
        self.connection = connection

    async def register(self, chat_id: int, username: Optional[str] = None) -> UserDTO:
        """Registers a new chat."""
        query = """
            INSERT INTO users (chat_id, username)
            VALUES (%s, %s)
            ON CONFLICT (chat_id) DO UPDATE
            SET username = EXCLUDED.username
            RETURNING chat_id, username
        """

        try:
            result = await self.connection.fetchrow(query, chat_id, username or "")
        except Exception:
            logger.exception("Error executing registration query")
            raise

        if not result:
            logger.error("No result returned for chat_id: %s", chat_id)
            raise ValueError(f"Failed to register chat {chat_id}")

        return UserDTO(user_id=result["chat_id"], username=result["username"])

    async def get_chat(self, chat_id: int) -> Optional[UserDTO]:
        """Retrieves a chat by its ID.

        Args:
            chat_id: The ID of the chat to retrieve.

        Returns:
            The UserDTO representing the chat, or None if not found.

        """
        try:
            query = """
            SELECT chat_id, username
            FROM users
            WHERE chat_id = %s
            """
            result = await self.connection.fetchrow(query, chat_id)
            if result:
                return UserDTO(user_id=result["chat_id"], username=result["username"])
        except Exception:
            logger.exception("Error getting chat")
            return None
        return None

    async def delete_chat(self, chat_id: int) -> None:
        """Deletes a chat by its ID.

        Args:
            chat_id: The ID of the chat to delete.

        """
        try:
            query = """
            DELETE FROM users
            WHERE chat_id = %s
            """
            await self.connection.execute(query, chat_id)
        except Exception:
            logger.exception("Error deleting chat")
            raise

    async def get_all_chats_ids(self, batch_size: int) -> AsyncGenerator[List[int], None]:
        """Retrieves all chat IDs in batches.

        Args:
            batch_size: The number of chat IDs to retrieve per batch.

        Yields:
            Batches of chat IDs.

        """
        try:
            offset = 0
            while True:
                query = """
                SELECT chat_id
                FROM users
                ORDER BY chat_id
                LIMIT %s OFFSET %s
                """
                rows = await self.connection.fetch(query, batch_size, offset)
                if not rows:
                    break

                chat_ids = [cast(int, row["chat_id"]) for row in rows]
                yield chat_ids

                if len(rows) < batch_size:
                    break

                offset += batch_size
        except Exception:
            logger.exception("Error getting all chat IDs")
            yield []
