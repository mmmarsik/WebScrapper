import contextlib
import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, Union, cast

from psycopg import AsyncConnection, DatabaseError
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

logger = logging.getLogger(__name__)


class SQLConnectionPool:
    """Class for managing SQL connections using psycopg3."""

    def __init__(self, connection_string: str, min_size: int = 2, max_size: int = 10) -> None:
        """Initialize the SQL connection.

        Args:
            connection_string: The connection string for the database.
            min_size: Minimum number of connections in the pool.
            max_size: Maximum number of connections in the pool.

        """
        self.connection_string = connection_string
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[AsyncConnectionPool] = None

    async def initialize(self) -> None:
        """Initialize the connection pool."""
        if self.pool is None or self.pool.closed:
            self.pool = AsyncConnectionPool(
                conninfo=self.connection_string,
                min_size=self.min_size,
                max_size=self.max_size,
                kwargs={"row_factory": dict_row},
            )
            await self.pool.wait()
            logger.info("SQL connection pool initialized")

    async def close(self) -> None:
        """Close the connection pool."""
        if self.pool and not self.pool.closed:
            await self.pool.close()
            logger.info("SQL connection pool closed")

    async def execute(
        self,
        query: str,
        *args: Union[str, float, bool, None, Tuple[Any, ...]],
    ) -> Optional[str]:
        """Execute a SQL query.

        Args:
            query: The SQL query to execute.
            *args: Arguments for the query.

        Returns:
            The status of the query execution.

        Raises:
            DatabaseError: If there's an error executing the query.

        """
        if not self.pool:
            await self.initialize()
        assert self.pool is not None

        try:
            async with self.pool.connection() as conn, conn.cursor() as cur:
                await cur.execute(query, args)
                await conn.commit()
                return cur.statusmessage
        except DatabaseError:
            logger.exception("Error executing query")
            raise

    async def fetch(
        self,
        query: str,
        *args: Union[str, float, bool, None, Tuple[Any, ...]],
    ) -> List[Dict[str, Any]]:
        """Fetch rows from a SQL query.

        Args:
            query: The SQL query to execute.
            *args: Arguments for the query.

        Returns:
            A list of dictionaries representing the rows.

        Raises:
            DatabaseError: If there's an error executing the query.

        """
        if not self.pool:
            await self.initialize()
        assert self.pool is not None

        try:
            async with self.pool.connection() as conn, conn.cursor() as cur:
                await cur.execute(query, args)
                rows = await cur.fetchall()
                return cast(List[Dict[str, Any]], rows)
        except DatabaseError:
            logger.exception("Error fetching data")
            raise

    async def fetchrow(
        self,
        query: str,
        *args: Union[str, float, bool, None, Tuple[Any, ...]],
    ) -> Optional[Dict[str, Any]]:
        """Fetch a single row from a SQL query.

        Args:
            query: The SQL query to execute.
            *args: Arguments for the query.

        Returns:
            A dictionary representing the row, or None if no row was found.

        Raises:
            DatabaseError: If there's an error executing the query.

        """
        if not self.pool:
            await self.initialize()
        assert self.pool is not None

        try:
            async with self.pool.connection() as conn, conn.cursor() as cur:
                await cur.execute(query, args)
                row = await cur.fetchone()
                return cast(Optional[Dict[str, Any]], row)
        except DatabaseError:
            logger.exception("Error fetching row")
            raise

    @contextlib.asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncConnection]:
        """Start a transaction.

        Returns:
            A connection with a transaction.

        Raises:
            DatabaseError: If there's an error executing the query.

        """
        if not self.pool:
            await self.initialize()
        assert self.pool is not None

        async with self.pool.connection() as conn:
            try:
                async with conn.transaction():
                    yield conn
            except DatabaseError:
                logger.exception("Error in transaction")
                raise
