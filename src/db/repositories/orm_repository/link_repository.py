import logging
from datetime import datetime
from typing import List

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import joinedload

from src.db.models import LinkMuteStatusORM, LinkORM, TagORM
from src.db.repositories.base import LinkAddError, LinkRepositoryInterface
from src.scrapper.models_dto import LinkDTO, TagDTO

logger = logging.getLogger(__name__)


class ORMLinkRepository(LinkRepositoryInterface):
    """ORM-based implementation of the LinkRepositoryInterface.

    Provides methods for managing links in the database using SQLAlchemy ORM.
    """

    def __init__(self, async_session_maker: async_sessionmaker[AsyncSession]) -> None:
        """Initializes the ORMLinkRepository with an asynchronous database session.

        Args:
            async_session_maker: The asynchronous database session maker.

        """
        self._async_session_maker = async_session_maker

    async def add_link(
        self,
        chat_id: int,
        url: str,
        tags: List[str],
        filters: List[str],
    ) -> LinkDTO:
        if not url:
            raise ValueError("Url cannot be empty")
        try:
            async with self._async_session_maker() as session:
                result = await session.execute(
                    select(LinkORM).where(LinkORM.chat_id == chat_id, LinkORM.url == url),
                )
                existing_link = result.scalars().first()

                tag_objects = []
                if tags:
                    tag_query = select(TagORM).where(TagORM.tag_name.in_(tags))
                    tag_result = await session.execute(tag_query)
                    existing_tags = {tag.tag_name: tag for tag in tag_result.scalars().all()}
                    for tag_name in tags:
                        if tag_name in existing_tags:
                            tag_objects.append(existing_tags[tag_name])
                        else:
                            new_tag = TagORM(name=tag_name)
                            session.add(new_tag)
                            await session.flush()
                            tag_objects.append(new_tag)

                if existing_link:
                    existing_link.tags = tag_objects
                    existing_link.filters = ",".join(filters) if filters else None

                    session.add(existing_link)
                    await session.commit()
                    await session.refresh(existing_link)
                    return self._to_dto(existing_link)

                new_link = LinkORM(
                    chat_id=chat_id,
                    url=url,
                    filters=",".join(filters) if filters else None,
                )
                new_link.tags = tag_objects
                new_link.mute_status = LinkMuteStatusORM(
                    link_id=new_link.link_id,
                    chat_id=new_link.chat_id,
                    muted=False,
                )
                session.add(new_link)
                await session.commit()
                await session.refresh(new_link)
                return self._to_dto(new_link)
        except SQLAlchemyError as e:
            logger.exception("Error adding/updating link")
            raise LinkAddError(f"Error adding/updating link: {e}") from e

    async def remove_link(self, chat_id: int, url: str) -> LinkDTO | None:
        """Removes a link from the database.

        Args:
            chat_id: The ID of the chat to which the link belongs.
            url: The URL of the link to remove.

        Returns:
            The LinkDTO representing the removed link, or None if the link was not found.

        Raises:
            ValueError: If the url is invalid.
            SQLAlchemyError: If there is a database error.

        """
        if not url:
            raise ValueError("Url cannot be empty")
        try:
            async with self._async_session_maker() as session:
                query = select(LinkORM).where(LinkORM.chat_id == chat_id, LinkORM.url == url)
                result = await session.execute(query)
                link = result.scalars().first()
                if link is None:
                    return None
                await session.delete(link)
                await session.commit()
                return self._to_dto(link)
        except SQLAlchemyError:
            logger.exception("Error removing link")
            raise

    async def list_links(
        self,
        chat_id: int,
    ) -> List[LinkDTO]:
        """Retrieves a list of links for a given chat in batches.

        Args:
            chat_id: The ID of the chat for which to retrieve links.

        Returns:
            List of LinkDTOs representing the retrieved links.

        Raises:
            SQLAlchemyError: If there is a database error.

        """
        try:
            async with self._async_session_maker() as session:
                query = select(LinkORM).where(LinkORM.chat_id == chat_id)
                result = await session.execute(query)
                links = result.scalars().all()
                return [self._to_dto(link) for link in links]
        except SQLAlchemyError:
            logger.exception("Error listing links")
            raise

    async def get_link(self, chat_id: int, url: str) -> LinkDTO | None:
        """Retrieves a specific link by its URL for a given chat.

        Args:
            chat_id: The ID of the chat to which the link belongs.
            url: The URL of the link to retrieve.

        Returns:
            The LinkDTO representing the link, or None if the link was not found.

        Raises:
            ValueError: If the url is invalid.
            SQLAlchemyError: If there is a database error.

        """
        if not url:
            raise ValueError("Url cannot be empty")
        try:
            async with self._async_session_maker() as session:
                query = (
                    select(LinkORM)
                    .where(LinkORM.chat_id == chat_id, LinkORM.url == url)
                    .options(joinedload(LinkORM.mute_status))
                )
                result = await session.execute(query)
                link = result.scalars().first()
                if link is None:
                    return None
                return self._to_dto(link)
        except SQLAlchemyError:
            logger.exception("Error getting link")
            raise

    def _to_dto(self, link: LinkORM) -> LinkDTO:
        """Converts a LinkORM object to a LinkDTO.

        Args:
            link: The LinkORM object to convert.

        Returns:
            The corresponding LinkDTO.

        """
        tags = [TagDTO(tag_name=tag.tag_name) for tag in link.tags] if link.tags else []
        filters = link.filters.split(",") if link.filters else []
        muted = link.mute_status.muted if link.mute_status else False
        last_updated = link.last_updated if isinstance(link.last_updated, datetime) else None
        return LinkDTO(
            chat_id=link.chat_id,
            url=link.url,
            last_updated=last_updated,
            tags=tags,
            filters=filters,
            muted=muted,
        )

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
            SQLAlchemyError: If there is a database error.

        """
        if not url:
            raise ValueError("Url cannot be empty")
        try:
            async with self._async_session_maker() as session:
                query = (
                    update(LinkORM)
                    .where(LinkORM.chat_id == chat_id, LinkORM.url == url)
                    .values(last_updated=last_updated)
                )
                result = await session.execute(query)
                await session.commit()
                return result.rowcount > 0
        except SQLAlchemyError:
            logger.exception("Error updating link last updated")
            raise

    async def get_links_by_tag(self, chat_id: int, tag: str) -> List[LinkDTO]:
        """Get all links for a chat with a specific tag.

        Args:
            chat_id: The ID of the chat to get links for.
            tag: The tag to filter links by.

        Returns:
            List[LinkDTO]: A list of all links for the chat with the specified tag.

        Raises:
            ValueError: If the tag is invalid.
            SQLAlchemyError: If there is a database error.

        """
        if not tag:
            raise ValueError("Tag cannot be empty")
        try:
            async with self._async_session_maker() as session:
                query = (
                    select(LinkORM)
                    .join(LinkORM.tags)
                    .where(LinkORM.chat_id == chat_id, TagORM.tag_name == tag)
                    .options(joinedload(LinkORM.mute_status), joinedload(LinkORM.tags))
                )
                result = await session.execute(query)
                links = result.unique().scalars().all()
                return [self._to_dto(link) for link in links]
        except SQLAlchemyError:
            logger.exception("Error getting links by tag")
            raise

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
            SQLAlchemyError: If there is a database error.

        """
        if not url:
            raise ValueError("Url cannot be empty")
        try:
            async with self._async_session_maker() as session:
                link_query = select(LinkORM).where(LinkORM.chat_id == chat_id, LinkORM.url == url)
                link_result = await session.execute(link_query)
                link = link_result.scalars().first()
                if not link:
                    return False

                mute_status_query = select(LinkMuteStatusORM).where(
                    LinkMuteStatusORM.link_id == link.link_id,
                )
                mute_status_result = await session.execute(mute_status_query)
                mute_status = mute_status_result.scalars().first()

                if mute_status:
                    mute_status.muted = muted
                else:
                    mute_status = LinkMuteStatusORM(
                        link_id=link.link_id,
                        chat_id=link.chat_id,
                        muted=muted,
                    )
                    session.add(mute_status)

                await session.commit()
                return True
        except SQLAlchemyError:
            logger.exception("Error updating link mute status")
            raise

    async def get_links_by_tag_and_chat_id(self, chat_id: int, tag_name: str) -> List[LinkDTO]:
        """Get all links for a chat with a specific tag.

        Args:
            chat_id: The ID of the chat to get links for.
            tag_name: The tag to filter links by.

        Returns:
            List[LinkDTO]: A list of all links for the chat with the specified tag.

        Raises:
            ValueError: If the tag name is invalid.
            SQLAlchemyError: If there is a database error.

        """
        if not tag_name:
            raise ValueError("Tag name cannot be empty")
        try:
            async with self._async_session_maker() as session:
                query = (
                    select(LinkORM)
                    .join(LinkORM.tags)
                    .where(LinkORM.chat_id == chat_id, TagORM.tag_name == tag_name)
                    .options(joinedload(LinkORM.mute_status))
                )
                result = await session.execute(query)
                links = result.unique().scalars().all()
                return [self._to_dto(link) for link in links]
        except SQLAlchemyError:
            logger.exception("Error getting links by tag and chat id")
            raise
