import asyncio
import contextlib
import uuid
from typing import AsyncGenerator, Dict, Generator, List

import pytest
import pytest_asyncio
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from testcontainers.postgres import PostgresContainer


async def ensure_user_exists(pool: AsyncConnectionPool, chat_id: int) -> None:
    """Ensure a user with the given chat_id exists in the users table."""
    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO users (chat_id, username) VALUES (%s, %s) ON CONFLICT DO NOTHING
            """,
            (chat_id, f"user_{uuid.uuid4().hex[:8]}"),
        )
        await conn.commit()


class PsycopgPoolWrapper:
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self._pool = pool

    @contextlib.asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncConnectionPool, None]:
        async with self._pool.connection() as conn:
            yield conn

    async def fetch(self, query: str, *args: List[str]) -> list[Dict[str, str]]:
        async with self._pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, args)
            return await cur.fetchall()

    async def fetchrow(self, query: str, *args: List[str]) -> Dict[str, str] | None:
        async with self._pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, args)
            return await cur.fetchone()


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def postgres_container() -> AsyncGenerator[PostgresContainer, None]:
    with PostgresContainer("postgres:13") as postgres:
        yield postgres


@pytest_asyncio.fixture
async def db_pool(
    postgres_container: PostgresContainer,
) -> AsyncGenerator[PsycopgPoolWrapper, None]:
    dsn = postgres_container.get_connection_url().replace("+psycopg2", "")
    pool = AsyncConnectionPool(dsn)
    await pool.open()
    wrapper = PsycopgPoolWrapper(pool)

    async with pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                chat_id BIGINT PRIMARY KEY,
                username VARCHAR(100) NULL
            );
            """,
        )
        await cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tracked_links (
                link_id SERIAL PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                url VARCHAR(255) NOT NULL,
                last_updated TIMESTAMP WITH TIME ZONE,
                filters VARCHAR(255),
                CONSTRAINT fk_user FOREIGN KEY (chat_id)
                    REFERENCES users (chat_id) ON DELETE CASCADE,
                CONSTRAINT unique_chat_url UNIQUE (chat_id, url)
            );
            """,
        )
        await cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tags (
                tag_id SERIAL PRIMARY KEY,
                tag_name VARCHAR(100) NOT NULL
                    CONSTRAINT unique_tag_name UNIQUE
            );
            """,
        )
        await cur.execute(
            """
            CREATE TABLE IF NOT EXISTS links_tags (
                link_id INT NOT NULL,
                tag_id INT NOT NULL,
                FOREIGN KEY (link_id)
                    REFERENCES tracked_links (link_id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id)
                    REFERENCES tags (tag_id) ON DELETE CASCADE,
                PRIMARY KEY (link_id, tag_id)
            );
            """,
        )
        await cur.execute(
            """
            CREATE TABLE IF NOT EXISTS link_mute_statuses (
                mute_status_id SERIAL PRIMARY KEY,
                link_id INT NOT NULL,
                chat_id BIGINT NOT NULL,
                muted BOOLEAN NOT NULL DEFAULT FALSE,
                FOREIGN KEY (link_id)
                    REFERENCES tracked_links (link_id) ON DELETE CASCADE,
                CONSTRAINT unique_link_chat UNIQUE (link_id, chat_id)
            );
            """,
        )
        await conn.commit()

    await ensure_user_exists(pool, 123)
    await ensure_user_exists(pool, 789)
    await ensure_user_exists(pool, 5)

    yield wrapper
    await pool.close()
