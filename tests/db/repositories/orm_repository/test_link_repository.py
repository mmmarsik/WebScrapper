import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from src.db.models import Base, UserORM
from src.db.repositories.orm_repository.link_repository import ORMLinkRepository


@pytest_asyncio.fixture
async def async_session_maker_fixture(
    postgres_container: PostgresContainer,
) -> async_sessionmaker[AsyncSession]:
    dsn = postgres_container.get_connection_url()
    dsn = dsn.replace("postgresql+psycopg2://", "postgresql+psycopg://")
    engine = create_async_engine(dsn, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def orm_link_repository(async_session_maker_fixture: async_sessionmaker) -> ORMLinkRepository:
    return ORMLinkRepository(async_session_maker_fixture)


@pytest.mark.asyncio
async def test_add_and_get_link(
    orm_link_repository: ORMLinkRepository,
    async_session_maker_fixture: async_sessionmaker,
) -> None:
    chat_id = 1

    async with async_session_maker_fixture() as session:
        new_user = UserORM(chat_id=chat_id, username="test_user")
        session.add(new_user)
        await session.commit()

    url = "https://example.com/orm"
    tags = ["python", "orm"]
    filters = ["filter1", "filter2"]

    added_link = await orm_link_repository.add_link(chat_id, url, tags, filters)
    assert added_link.chat_id == chat_id
    assert added_link.url == url
    returned_tag_names = {tag.tag_name for tag in added_link.tags}
    assert returned_tag_names == set(tags)
    assert added_link.filters == filters
    assert added_link.muted is False

    fetched_link = await orm_link_repository.get_link(chat_id, url)
    assert fetched_link is not None
    assert fetched_link.chat_id == chat_id
    assert fetched_link.url == url
    assert {tag.tag_name for tag in fetched_link.tags} == set(tags)
    assert fetched_link.filters == filters


@pytest.mark.asyncio
async def test_remove_link(
    orm_link_repository: ORMLinkRepository,
    async_session_maker_fixture: async_sessionmaker,
) -> None:
    chat_id = 2

    async with async_session_maker_fixture() as session:
        new_user = UserORM(chat_id=chat_id, username="remove_user")
        session.add(new_user)
        await session.commit()

    url = "https://example.com/remove"
    tags = ["remove", "test"]
    filters = ["filter_remove"]

    added_link = await orm_link_repository.add_link(chat_id, url, tags, filters)
    assert added_link is not None

    removed_link = await orm_link_repository.remove_link(chat_id, url)
    assert removed_link is not None

    fetched_link = await orm_link_repository.get_link(chat_id, url)
    assert fetched_link is None


@pytest.mark.asyncio
async def test_update_link(
    orm_link_repository: ORMLinkRepository,
    async_session_maker_fixture: async_sessionmaker,
) -> None:
    chat_id = 3

    async with async_session_maker_fixture() as session:
        new_user = UserORM(chat_id=chat_id, username="update_user")
        session.add(new_user)
        await session.commit()

    url = "https://example.com/update"
    initial_tags = ["initial", "link"]
    initial_filters = ["init_filter"]

    added_link = await orm_link_repository.add_link(chat_id, url, initial_tags, initial_filters)
    assert added_link is not None

    updated_tags = ["updated", "orm"]
    updated_filters = ["updated_filter1", "updated_filter2"]
    updated_link = await orm_link_repository.add_link(chat_id, url, updated_tags, updated_filters)

    assert updated_link is not None
    assert updated_link.chat_id == chat_id
    assert updated_link.url == url
    assert {tag.tag_name for tag in updated_link.tags} == set(updated_tags)
    assert updated_link.filters == updated_filters


@pytest.mark.asyncio
async def test_get_links_by_tag(
    orm_link_repository: ORMLinkRepository,
    async_session_maker_fixture: async_sessionmaker,
) -> None:
    chat_id = 4

    async with async_session_maker_fixture() as session:
        new_user = UserORM(chat_id=chat_id, username="tag_user")
        session.add(new_user)
        await session.commit()

    url1 = "https://example.com/link1"
    url2 = "https://example.com/link2"
    tags1 = ["common", "alpha"]
    filters1 = ["filter1"]
    tags2 = ["common", "beta"]
    filters2 = ["filter2"]

    await orm_link_repository.add_link(chat_id, url1, tags1, filters1)
    await orm_link_repository.add_link(chat_id, url2, tags2, filters2)

    links = await orm_link_repository.get_links_by_tag(chat_id, "common")
    returned_urls = {link.url for link in links}
    assert url1 in returned_urls
    assert url2 in returned_urls


@pytest.mark.asyncio
async def test_get_links_by_tag_and_chat_id(
    orm_link_repository: ORMLinkRepository,
    async_session_maker_fixture: async_sessionmaker,
) -> None:
    chat_id = 5

    async with async_session_maker_fixture() as session:
        new_user = UserORM(chat_id=chat_id, username="tag_and_chat_user")
        session.add(new_user)
        await session.commit()

    url1 = "https://example.com/chtag1"
    url2 = "https://example.com/chtag2"
    tags1 = ["special", "unique"]
    filters1 = ["f1"]
    tags2 = ["other", "special"]
    filters2 = ["f2"]

    await orm_link_repository.add_link(chat_id, url1, tags1, filters1)
    await orm_link_repository.add_link(chat_id, url2, tags2, filters2)

    links_special = await orm_link_repository.get_links_by_tag_and_chat_id(chat_id, "special")
    returned_urls = {link.url for link in links_special}
    assert url1 in returned_urls
    assert url2 in returned_urls

    unique_links = await orm_link_repository.get_links_by_tag_and_chat_id(chat_id, "unique")
    assert len(unique_links) == 1
    assert unique_links[0].url == url1
