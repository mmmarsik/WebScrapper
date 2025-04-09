import logging
from typing import List

from psycopg import DatabaseError

from src.db.repositories.base import TagRepositoryInterface
from src.db.repositories.sql_repository.sql_pool_manager import SQLConnectionPool
from src.scrapper.models_dto import TagDTO

logger = logging.getLogger(__name__)


class SQLTagRepository(TagRepositoryInterface):
    """SQL implementation of the tag repository interface."""

    def __init__(self, connection: SQLConnectionPool) -> None:
        """Initialize the SQL tag repository.

        Args:
            connection: The SQL connection.

        """
        self.connection = connection

    async def get_or_create_tag(self, tag_name: str) -> TagDTO:
        """Retrieves a tag by name, or creates a new one if it doesn't exist.

        Args:
            tag_name: The name of the tag.

        Returns:
            The TagDTO instance.

        Raises:
            ValueError: If the tag name is invalid or creation failed.
            DatabaseError: If there is a database error.

        """
        if not tag_name:
            raise ValueError("Tag name cannot be empty")

        query = """
            INSERT INTO tags (tag_name)
            VALUES (%s)
            ON CONFLICT (tag_name) DO UPDATE
            SET tag_name = EXCLUDED.tag_name
            RETURNING id, tag_name
        """

        try:
            result = await self.connection.fetchrow(query, tag_name)
        except Exception as e:
            logger.exception("Database error while adding tag")
            raise DatabaseError("Failed to process tag operation") from e

        if result is None:
            raise ValueError(f"Failed to get or create tag: {tag_name}")

        return TagDTO(tag_name=result["tag_name"])

    async def remove_tag(self, tag_name: str) -> bool:
        """Remove a tag from the repository.

        Args:
            tag_name: The name of the tag to remove.

        Returns:
            bool: True if the tag was removed, False otherwise.

        Raises:
            ValueError: If the tag name is invalid.
            DatabaseError: If there is a database error.

        """
        if not tag_name:
            raise ValueError("Tag name cannot be empty")
        try:
            tag_query = """
            SELECT id FROM tags WHERE tag_name = %s
            """
            tag_row = await self.connection.fetchrow(tag_query, tag_name)
            if not tag_row:
                return False

            tag_id = tag_row["id"]

            link_tag_query = """
            DELETE FROM links_tags
            WHERE tag_id = %s
            """
            await self.connection.execute(link_tag_query, tag_id)

            delete_tag_query = """
            DELETE FROM tags
            WHERE id = %s
            RETURNING id
            """
            result = await self.connection.fetchrow(delete_tag_query, tag_id)
        except Exception:
            logger.exception("Error removing tag")
            raise

        return result is not None

    async def get_tag(self, tag_name: str) -> TagDTO | None:
        """Get a tag from the repository.

        Args:
            tag_name: The name of the tag to get.

        Returns:
            TagDTO | None: The tag, or None if not found.

        Raises:
            ValueError: If the tag name is invalid.
            DatabaseError: If there is a database error.

        """
        if not tag_name:
            raise ValueError("Tag name cannot be empty")
        try:
            query = """
            SELECT id, tag_name
            FROM tags
            WHERE tag_name = %s
            """
            result = await self.connection.fetchrow(query, tag_name)
            if not result:
                return None
            return TagDTO(tag_name=result["tag_name"])
        except Exception:
            logger.exception("Error getting tag")
            raise

    async def get_all_tags(self) -> List[TagDTO]:
        """Get all tags from the repository.

        Returns:
            List[TagDTO]: A list of all tags.

        Raises:
            DatabaseError: If there is a database error.

        """
        try:
            query = """
            SELECT id, tag_name
            FROM tags
            """
            result = await self.connection.fetch(query)
            return [TagDTO(tag_name=row["tag_name"]) for row in result]
        except Exception:
            logger.exception("Error getting all tags")
            raise
