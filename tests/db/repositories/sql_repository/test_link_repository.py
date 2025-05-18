import pytest
import pytest_asyncio

from src.db.repositories.sql_repository.link_repository import SQLLinkRepository
from src.scrapper.models_dto import LinkDTO


@pytest.fixture
def sample_link_data() -> dict:
    return {
        "chat_id": 123,
        "url": "https://test.com/sql",
        "tags": ["python", "sql"],
        "filters": ["filter1", "filter2"],
    }


@pytest_asyncio.fixture
async def repository(db_pool: SQLLinkRepository) -> SQLLinkRepository:
    return SQLLinkRepository(db_pool)


@pytest.mark.asyncio  # type: ignore
async def test_add_and_get_link(repository: SQLLinkRepository, sample_link_data: dict) -> None:
    added_link = await repository.add_link(
        chat_id=sample_link_data["chat_id"],
        url=sample_link_data["url"],
        tags=sample_link_data["tags"],
        filters=sample_link_data["filters"],
    )
    assert isinstance(added_link, LinkDTO)
    assert added_link.chat_id == sample_link_data["chat_id"]
    assert added_link.url == sample_link_data["url"]
    assert {tag.tag_name for tag in added_link.tags} == set(sample_link_data["tags"])
    assert added_link.filters == sample_link_data["filters"]
    assert added_link.muted is False

    retrieved = await repository.get_link(sample_link_data["chat_id"], sample_link_data["url"])
    assert retrieved is not None
    assert retrieved.chat_id == sample_link_data["chat_id"]
    assert retrieved.url == sample_link_data["url"]
    assert {tag.tag_name for tag in retrieved.tags} == set(sample_link_data["tags"])
    assert retrieved.filters == sample_link_data["filters"]
    assert retrieved.muted is False


@pytest.mark.asyncio  # type: ignore
async def test_remove_link(repository: SQLLinkRepository, sample_link_data: dict) -> None:
    added_link = await repository.add_link(
        chat_id=sample_link_data["chat_id"],
        url=sample_link_data["url"],
        tags=sample_link_data["tags"],
        filters=sample_link_data["filters"],
    )
    assert added_link is not None

    removed_link = await repository.remove_link(
        sample_link_data["chat_id"],
        sample_link_data["url"],
    )
    assert removed_link is not None
    assert removed_link.url == sample_link_data["url"]

    retrieved = await repository.get_link(sample_link_data["chat_id"], sample_link_data["url"])
    assert retrieved is None


@pytest.mark.asyncio  # type: ignore
async def test_get_links_by_tag(repository: SQLLinkRepository) -> None:
    chat_id = 789
    await repository.add_link(chat_id, "https://example.com/tag1", ["tag1", "common"], [])
    await repository.add_link(chat_id, "https://example.com/tag2", ["tag2", "common"], [])
    await repository.add_link(chat_id, "https://example.com/tag3", ["tag3"], [])

    common_links = await repository.get_links_by_tag(chat_id, "common")
    correct_len = 2
    assert len(common_links) == correct_len
    assert all(
        link.url in ["https://example.com/tag1", "https://example.com/tag2"]
        for link in common_links
    )

    tag1_links = await repository.get_links_by_tag(chat_id, "tag1")
    assert len(tag1_links) == 1
    assert tag1_links[0].url == "https://example.com/tag1"

    tag3_links = await repository.get_links_by_tag(chat_id, "tag3")
    assert len(tag3_links) == 1
    assert tag3_links[0].url == "https://example.com/tag3"

    no_tag_links = await repository.get_links_by_tag(chat_id, "nonexistent")
    assert len(no_tag_links) == 0


@pytest.mark.asyncio  # type: ignore
async def test_update_link_mute_status(
    repository: SQLLinkRepository,
    sample_link_data: dict,
) -> None:
    await repository.add_link(
        chat_id=sample_link_data["chat_id"],
        url=sample_link_data["url"],
        tags=sample_link_data["tags"],
        filters=sample_link_data["filters"],
    )

    retrieved = await repository.get_link(sample_link_data["chat_id"], sample_link_data["url"])
    assert retrieved.muted is False

    await repository.update_link_mute_status(
        sample_link_data["chat_id"],
        sample_link_data["url"],
        True,
    )
    retrieved = await repository.get_link(sample_link_data["chat_id"], sample_link_data["url"])
    assert retrieved.muted is True

    await repository.update_link_mute_status(
        sample_link_data["chat_id"],
        sample_link_data["url"],
        False,
    )
    retrieved = await repository.get_link(sample_link_data["chat_id"], sample_link_data["url"])
    assert retrieved.muted is False


@pytest.mark.asyncio
async def test_get_links_by_tag_and_chat_id(repository: SQLLinkRepository) -> None:
    chat_id = 5

    url1 = "https://example.com/chtag1"
    url2 = "https://example.com/chtag2"
    tags1 = ["special", "unique"]
    filters1 = ["f1"]
    tags2 = ["other", "special"]
    filters2 = ["f2"]

    await repository.add_link(chat_id, url1, tags1, filters1)
    await repository.add_link(chat_id, url2, tags2, filters2)

    links_special = await repository.get_links_by_tag_and_chat_id(chat_id, "special")
    returned_urls = {link.url for link in links_special}
    assert url1 in returned_urls
    assert url2 in returned_urls
