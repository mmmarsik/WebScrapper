import logging
from datetime import datetime
from typing import Any, Dict, List, cast

from psycopg import AsyncConnection, DatabaseError
from psycopg.rows import dict_row

from src.db.repositories.base import LinkAddError, LinkRepositoryInterface
from src.db.repositories.sql_repository.sql_pool_manager import SQLConnectionPool
from src.scrapper.models_dto import LinkDTO, TagDTO

logger = logging.getLogger(__name__)


class SQLLinkRepository(LinkRepositoryInterface):
    """SQL implementation of the link repository interface."""

    def __init__(self, connection_pool: SQLConnectionPool) -> None:
        """Initialize the SQL link repository.

        Args:
            connection_pool: The SQL connection pool.

        Return:
            None

        """
        self._connection_pool = connection_pool

    async def add_link(
        self,
        chat_id: int,
        url: str,
        tags: List[str],
        filters: List[str],
    ) -> LinkDTO:
        """Add a link to the repository.

        Args:
            chat_id: The ID of the chat to add the link to.
            url: The URL of the link to add.
            tags: The tags to associate with the link.
            filters: The filters to apply to the link.

        Returns:
            LinkDTO: The added link.

        Raises:
            LinkAddError: If the link couldn't be added.
            ValueError: If the url is invalid.
            DatabaseError: If there is a database error.

        """
        if not url:
            raise ValueError("Url cannot be empty")
        try:
            async with self._connection_pool.transaction() as conn:
                link_row = await self._execute_link_insert(conn, chat_id, url, filters)
                await self._process_tags(conn, link_row["link_id"], tags)
                await self._create_link_mute_status(conn, link_row["link_id"], chat_id)
                return LinkDTO(
                    chat_id=link_row["chat_id"],
                    url=link_row["url"],
                    last_updated=link_row.get("last_updated"),
                    tags=[TagDTO(tag_name=name) for name in tags],
                    filters=filters,
                    muted=False,
                )

        except Exception:
            logger.exception("Error adding link")
            raise

    async def _execute_link_insert(
        self,
        conn: AsyncConnection,
        chat_id: int,
        url: str,
        filters: List[str],
    ) -> Dict[str, Any]:
        """Execute link insertion and return result row.

        Args:
            conn: The database connection.
            chat_id: The ID of the chat.
            url: The URL of the link.
            filters: The filters for the link.

        Returns:
            Dict[str, Any]: The row data of the inserted link.

        Raises:
            LinkAddError: If the link couldn't be added or updated.
            DatabaseError: If there is a database error.

        """
        filters_str = ",".join(filters) if filters else None
        query = """
            INSERT INTO tracked_links (chat_id, url, filters)
            VALUES (%s, %s, %s)
            ON CONFLICT (chat_id, url) DO UPDATE
            SET filters = %s
            RETURNING link_id, chat_id, url, last_updated, filters
        """
        try:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, (chat_id, url, filters_str, filters_str))
                if not (link_row := await cur.fetchone()):
                    raise LinkAddError(f"Failed to add/update link: {url} for chat_id: {chat_id}")
        except DatabaseError:
            logger.exception("Error executing link insert query")
            raise
        return link_row

    async def _process_tags(self, conn: AsyncConnection, link_id: int, tags: List[str]) -> None:
        """Process tags association.

        Args:
            conn: The database connection.
            link_id: The ID of the link.
            tags: The list of tags to associate.

        Raises:
            DatabaseError: If there is a database error.

        """
        try:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM links_tags WHERE link_id = %s", (link_id,))

            tag_ids: List[int] = []
            for tag in tags:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(
                        "INSERT INTO tags (tag_name) VALUES (%s) ON CONFLICT (tag_name) DO UPDATE "
                        "SET tag_name = EXCLUDED.tag_name RETURNING id",
                        (tag,),
                    )
                    if tag_row := await cur.fetchone():
                        tag_ids.append(tag_row["id"])

            for tag_id in tag_ids:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "INSERT INTO links_tags (link_id, tag_id) VALUES (%s, %s) \
                            ON CONFLICT DO NOTHING",
                        (link_id, tag_id),
                    )
        except DatabaseError:
            logger.exception("Error processing tags")
            raise

    async def _create_link_mute_status(
        self,
        conn: AsyncConnection,
        link_id: int,
        chat_id: int,
    ) -> None:
        """Create a link mute status for a link.

        Args:
            conn: The database connection.
            link_id: The ID of the link.
            chat_id: The ID of the chat.

        Raises:
            DatabaseError: If there is a database error.

        """
        try:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO link_mute_statuses (link_id, chat_id, muted) VALUES (%s, %s, %s) \
                        ON CONFLICT DO NOTHING",
                    (link_id, chat_id, False),
                )
        except Exception:
            logger.exception("Error creating link mute status")
            raise

    async def remove_link(self, chat_id: int, url: str) -> LinkDTO | None:
        """Remove a link from the repository.

        Args:
            chat_id: The ID of the chat to remove the link from.
            url: The URL of the link to remove.

        Returns:
            Optional[LinkDTO]: The removed link, or None if it wasn't found.

        Raises:
            ValueError: If the url is invalid.
            DatabaseError: If there is a database error.

        """
        if not url:
            raise ValueError("Url cannot be empty")
        try:
            link = await self.get_link(chat_id, url)
            if not link:
                return None

            query = """
            DELETE FROM tracked_links
            WHERE chat_id = %s AND url = %s
            RETURNING link_id
            """
            result = await self._connection_pool.fetchrow(query, chat_id, url)
            result = cast(Dict[str, Any], result)
        except Exception:
            logger.exception("Error removing link")
            raise

        return link if result else None

    async def list_links(self, chat_id: int) -> List[LinkDTO]:
        """List all links for a chat.

        Args:
            chat_id: The ID of the chat to list links for.

        Returns:
            List[LinkDTO]: A list of all links for the chat.

        Raises:
            DatabaseError: If there is a database error.

        """
        try:
            query = """
            SELECT l.link_id, l.chat_id, l.url, l.last_updated, l.filters, \
                COALESCE(lm.muted, FALSE) as muted
            FROM tracked_links l
            LEFT JOIN link_mute_statuses lm ON l.link_id = lm.link_id
            WHERE l.chat_id = %s
            """
            link_rows = await self._connection_pool.fetch(query, chat_id)

            links: List[LinkDTO] = []
            for link_row in link_rows:
                tags_query = """
                SELECT t.id, t.name
                FROM tags t
                JOIN links_tags lt ON t.id = lt.tag_id
                WHERE lt.link_id = %s
                """
                tag_rows = await self._connection_pool.fetch(tags_query, link_row["link_id"])

                tag_dtos = [TagDTO(tag_name=tag_row["name"]) for tag_row in tag_rows]
                filters = link_row["filters"].split(",") if link_row["filters"] else []

                links.append(
                    LinkDTO(
                        chat_id=link_row["chat_id"],
                        url=link_row["url"],
                        last_updated=link_row.get("last_updated"),
                        tags=tag_dtos,
                        filters=filters,
                        muted=link_row["muted"],
                    ),
                )

        except Exception:
            logger.exception("Error listing links")
            raise

        return links

    async def get_link(self, chat_id: int, url: str) -> LinkDTO | None:
        """Get a link from the repository.

        Args:
            chat_id: The ID of the chat to get the link from.
            url: The URL of the link to get.

        Returns:
            Optional[LinkDTO]: The link, or None if it wasn't found.

        Raises:
            ValueError: If the url is invalid.
            DatabaseError: If there is a database error.

        """
        if not url:
            raise ValueError("Url cannot be empty")
        try:
            query = """
            SELECT l.link_id, l.chat_id, l.url, l.last_updated, l.filters, \
                COALESCE(lm.muted, FALSE) as muted
            FROM tracked_links l
            LEFT JOIN link_mute_statuses lm ON l.link_id = lm.link_id
            WHERE l.chat_id = %s AND l.url = %s
            """
            link_row = await self._connection_pool.fetchrow(query, chat_id, url)
            link_row = cast(Dict[str, Any], link_row)

            if not link_row:
                return None

            tags_query = """
            SELECT t.id, t.name
            FROM tags t
            JOIN links_tags lt ON t.id = lt.tag_id
            WHERE lt.link_id = %s
            """
            tag_rows = await self._connection_pool.fetch(tags_query, link_row["link_id"])

            tag_dtos = [TagDTO(tag_name=tag_row["tag_name"]) for tag_row in tag_rows]
            filters = link_row["filters"].split(",") if link_row["filters"] else []

            return LinkDTO(
                chat_id=link_row["chat_id"],
                url=link_row["url"],
                last_updated=link_row["last_updated"],
                tags=tag_dtos,
                filters=filters,
                muted=link_row["muted"],
            )
        except Exception:
            logger.exception("Error getting link")
            raise

    async def update_link_last_updated(
        self,
        chat_id: int,
        url: str,
        last_updated: datetime,
    ) -> bool:
        """Update the last updated time for a link.

        Args:
            chat_id: The ID of the chat the link belongs to.
            url: The URL of the link to update.
            last_updated: The new last updated time.

        Returns:
            bool: True if the link was updated, False otherwise.

        Raises:
            ValueError: If the url is invalid.
            DatabaseError: If there is a database error.

        """
        if not url:
            raise ValueError("Url cannot be empty")
        try:
            query = """
            UPDATE tracked_links
            SET last_updated = %s
            WHERE chat_id = %s AND url = %s
            RETURNING link_id
            """
            result = await self._connection_pool.fetchrow(
                query,
                last_updated.isoformat(),
                chat_id,
                url,
            )
            result = cast(Dict[str, Any], result)
        except Exception:
            logger.exception("Error updating link last updated")
            raise

        return result is not None

    async def get_links_by_tag(self, chat_id: int, tag: str) -> List[LinkDTO]:
        """Get all links for a chat with a specific tag.

        Args:
            chat_id: The ID of the chat to get links for.
            tag: The tag to filter links by.

        Returns:
            List[LinkDTO]: A list of all links for the chat with the specified tag.

        Raises:
            ValueError: If the tag is invalid.
            DatabaseError: If there is a database error.

        """
        if not tag:
            raise ValueError("Tag cannot be empty")
        try:
            query = """
            SELECT l.link_id, l.chat_id, l.url, l.last_updated, l.filters, \
                  COALESCE(lm.muted, FALSE) as muted
            FROM tracked_links l
            JOIN links_tags lt ON l.link_id = lt.link_id
            JOIN tags t ON lt.tag_id = t.id
            LEFT JOIN link_mute_statuses lm ON l.link_id = lm.link_id
            WHERE l.chat_id = %s AND t.name = %s
            """
            link_rows = await self._connection_pool.fetch(query, chat_id, tag)

            links: List[LinkDTO] = []
            for link_row in link_rows:
                tags_query = """
                SELECT t.id, t.name
                FROM tags t
                JOIN links_tags lt ON t.id = lt.tag_id
                WHERE lt.link_id = %s
                """
                tag_rows = await self._connection_pool.fetch(tags_query, link_row["link_id"])

                tag_dtos = [TagDTO(tag_name=tag_row["name"]) for tag_row in tag_rows]
                filters = link_row["filters"].split(",") if link_row["filters"] else []

                links.append(
                    LinkDTO(
                        chat_id=link_row["chat_id"],
                        url=link_row["url"],
                        last_updated=link_row["last_updated"],
                        tags=tag_dtos,
                        filters=filters,
                        muted=link_row["muted"],
                    ),
                )

        except Exception:
            logger.exception("Error getting links by tag")
            raise

        return links

    async def update_link_mute_status(self, chat_id: int, url: str, muted: bool) -> bool:
        """Update the mute status for a link.

        Args:
            chat_id: The ID of the chat the link belongs to.
            url: The URL of the link to update.
            muted: The new mute status.

        Returns:
            bool: True if the link was updated, False otherwise.

        Raises:
            ValueError: If the url is invalid.
            DatabaseError: If there is a database error.

        """
        if not url:
            raise ValueError("Url cannot be empty")
        try:
            link_query = """
            SELECT link_id
            FROM tracked_links
            WHERE chat_id = %s AND url = %s
            """
            link_row = await self._connection_pool.fetchrow(link_query, chat_id, url)
            if not link_row:
                return False

            query = """
            INSERT INTO link_mute_statuses (link_id, muted)
            VALUES (%s, %s)
            ON CONFLICT (link_id) DO UPDATE
            SET muted = %s
            RETURNING link_id
            """
            result = await self._connection_pool.fetchrow(query, link_row["link_id"], muted, muted)
            result = cast(Dict[str, Any], result)
        except Exception:
            logger.exception("Error updating link mute status")
            raise

        return result is not None

    async def get_links_by_tag_and_chat_id(self, chat_id: int, tag_name: str) -> List[LinkDTO]:
        """Get all links for a chat with a specific tag.

        Args:
            chat_id: The ID of the chat to get links for.
            tag_name: The tag to filter links by.

        Returns:
            List[LinkDTO]: A list of all links for the chat with the specified tag.

        Raises:
            ValueError: If the tag name is invalid.
            DatabaseError: If there is a database error.

        """
        if not tag_name:
            raise ValueError("Tag name cannot be empty")
        try:
            query = """
            SELECT l.link_id, l.chat_id, l.url, l.last_updated, l.filters, \
                COALESCE(lm.muted, FALSE) as muted
            FROM tracked_links l
            JOIN links_tags lt ON l.link_id = lt.link_id
            JOIN tags t ON lt.tag_id = t.id
            LEFT JOIN link_mute_statuses lm ON l.link_id = lm.link_id
            WHERE l.chat_id = %s AND t.name = %s
            """
            link_rows = await self._connection_pool.fetch(query, chat_id, tag_name)

            links: List[LinkDTO] = []
            for link_row in link_rows:
                tags_query = """
                SELECT t.id, t.name
                FROM tags t
                JOIN links_tags lt ON t.id = lt.tag_id
                WHERE lt.link_id = %s
                """
                tag_rows = await self._connection_pool.fetch(tags_query, link_row["link_id"])

                tag_dtos = [TagDTO(tag_name=tag_row["tag_name"]) for tag_row in tag_rows]
                filters = link_row["filters"].split(",") if link_row["filters"] else []

                links.append(
                    LinkDTO(
                        chat_id=link_row["chat_id"],
                        url=link_row["url"],
                        last_updated=link_row["last_updated"],
                        tags=tag_dtos,
                        filters=filters,
                        muted=link_row["muted"],
                    ),
                )

        except Exception:
            logger.exception("Error getting links by tag")
            raise

        return links
