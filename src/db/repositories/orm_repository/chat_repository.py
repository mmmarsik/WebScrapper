import logging
from typing import AsyncGenerator, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.models import UserORM
from src.db.repositories.base import ChatRepositoryInterface
from src.scrapper.models_dto import UserDTO

logger = logging.getLogger(__name__)


class ORMChatRepository(ChatRepositoryInterface):
    """ORM-based implementation of the ChatRepositoryInterface.

    Provides methods for managing chat data in the database using SQLAlchemy ORM.
    """

    def __init__(self, async_session_maker: async_sessionmaker[AsyncSession]) -> None:
        """Initializes the ORMChatRepository with an asynchronous database session.

        Args:
            async_session_maker: The asynchronous database session maker.

        """
        self._async_sessionmaker = async_session_maker

    async def register(self, chat_id: int, username: Optional[str] = None) -> UserDTO:
        """Registers a new chat in the database.

        Args:
            chat_id: The ID of the chat to register.
            username: The username associated with the chat (optional).

        Returns:
            The UserDTO representing the registered chat.

        """
        async with self._async_sessionmaker() as session:
            user = UserORM(chat_id=chat_id, username=username)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return UserDTO(user_id=user.chat_id, username=user.username)

    async def get_chat(self, chat_id: int) -> UserDTO | None:
        """Retrieves a chat from the database by its ID.

        Args:
            chat_id: The ID of the chat to retrieve.

        Returns:
            The UserDTO representing the chat, or None if the chat was not found.

        """
        async with self._async_sessionmaker() as session:
            user = await session.get(UserORM, chat_id)
            if not user:
                return None

            return UserDTO(user_id=user.chat_id, username=user.username)

    async def delete_chat(self, chat_id: int) -> None:
        """Deletes a chat from the database by its ID.

        Args:
            chat_id: The ID of the chat to delete.

        """
        async with self._async_sessionmaker() as session:
            user = await session.get(UserORM, chat_id)
            if not user:
                return
            await session.delete(user)
            await session.commit()

    async def get_all_chats_ids(self, batch_size: int) -> AsyncGenerator[List[int], None]:
        """Retrieves all chat IDs from the database in batches.

        Args:
            batch_size: The number of chat IDs to retrieve per batch.

        Yields:
            Batches of chat IDs.

        """
        offset = 0
        while True:
            async with self._async_sessionmaker() as session:
                query = select(UserORM.chat_id).offset(offset).limit(batch_size)
                result = await session.execute(query)
                batch = list(result.scalars().all())
                if not batch:
                    break
                yield batch
                offset += batch_size
