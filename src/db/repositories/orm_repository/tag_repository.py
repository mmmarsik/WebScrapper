import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.models import TagORM
from src.db.repositories.base import TagRepositoryInterface
from src.scrapper.models_dto import TagDTO

logger = logging.getLogger(__name__)


class ORMTagRepository(TagRepositoryInterface):
    def __init__(self, async_session_maker: async_sessionmaker[AsyncSession]) -> None:
        """Initializes the ORMTagRepository with an asynchronous database session.

        Args:
            async_session_maker: The asynchronous database session maker.

        Returns:
            None

        """
        self._async_session_maker = async_session_maker

    async def get_or_create_tag(self, tag_name: str) -> TagDTO:
        """Retrieves a tag by name if it exists, or creates a new one.

        Args:
            tag_name (str): The name of the tag.

        Returns:
            TagDTO: The tag DTO instance.

        Raises:
            ValueError: If the tag name is invalid.
            SQLAlchemyError: If there is a database error.

        """
        if not tag_name:
            raise ValueError("Tag name cannot be empty")
        try:
            async with self._async_session_maker() as session:
                query = select(TagORM).where(TagORM.tag_name == tag_name)
                result = await session.execute(query)
                tag = result.scalars().first()
                if tag:
                    return TagDTO(tag_name=tag.tag_name)
                tag = TagORM(tag_name=tag_name)
                session.add(tag)
                await session.commit()
                await session.refresh(tag)
                return TagDTO(tag_name=tag.tag_name)
        except SQLAlchemyError:
            logger.exception("Error getting or creating tag")
            raise

    async def remove_tag(self, tag_name: str) -> bool:
        """Removes a tag by name.

        Args:
            tag_name: The name of the tag to remove.

        Returns:
            True if the tag was removed, False otherwise.

        Raises:
            ValueError: If the tag name is invalid.
            SQLAlchemyError: If there is a database error.

        """
        if not tag_name:
            raise ValueError("Tag name cannot be empty")
        try:
            async with self._async_session_maker() as session:
                query = select(TagORM).where(TagORM.tag_name == tag_name)
                result = await session.execute(query)
                tag = result.scalars().first()
                if not tag:
                    return False
                await session.delete(tag)
                await session.commit()
                return True
        except SQLAlchemyError:
            logger.exception("Error removing tag")
            raise

    async def get_tag(self, tag_name: str) -> TagDTO | None:
        """Retrieves a tag by name.

        Args:
            tag_name: The name of the tag to retrieve.

        Returns:
            The TagDTO instance, or None if not found.

        Raises:
            ValueError: If the tag name is invalid.
            SQLAlchemyError: If there is a database error.

        """
        if not tag_name:
            raise ValueError("Tag name cannot be empty")
        try:
            async with self._async_session_maker() as session:
                query = select(TagORM).where(TagORM.tag_name == tag_name)
                result = await session.execute(query)
                tag = result.scalars().first()
                if not tag:
                    return None
                return TagDTO(tag_name=tag.tag_name)
        except SQLAlchemyError:
            logger.exception("Error getting tag")
            raise

    async def get_all_tags(self) -> List[TagDTO]:
        """Retrieves all tags.

        Returns:
            A list of TagDTO instances.

        Raises:
            SQLAlchemyError: If there is a database error.

        """
        try:
            async with self._async_session_maker() as session:
                query = select(TagORM)
                result = await session.execute(query)
                tags = result.scalars().all()
                return [TagDTO(tag_name=tag.tag_name) for tag in tags]
        except SQLAlchemyError:
            logger.exception("Error getting all tags")
            raise
