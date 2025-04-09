import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncGenerator, List, Optional

from src.scrapper.models_dto import LinkDTO, TagDTO, UserDTO

logger = logging.getLogger(__name__)


class LinkAddError(Exception):
    """Custom exception for link adding errors."""


class ChatRepositoryInterface(ABC):
    """Abstract base class for chat repository operations.

    Defines the contract for managing chat data, including registration,
    retrieval, and deletion of chats.
    """

    @abstractmethod
    async def register(self, chat_id: int, username: Optional[str] = None) -> UserDTO:
        """Registers a new chat.

        Args:
            chat_id: The ID of the chat to register.
            username: The username associated with the chat (optional).

        Returns:
            The UserDTO representing the registered chat.

        """
        ...

    @abstractmethod
    async def get_chat(self, chat_id: int) -> UserDTO | None:
        """Retrieves a chat by its ID.

        Args:
            chat_id: The ID of the chat to retrieve.

        Returns:
            The UserDTO representing the chat, or None if not found.

        """
        ...

    @abstractmethod
    async def delete_chat(self, chat_id: int) -> None:
        """Deletes a chat by its ID.

        Args:
            chat_id: The ID of the chat to delete.

        """
        ...

    @abstractmethod
    def get_all_chats_ids(self, batch_size: int) -> AsyncGenerator[List[int], None]:
        """Retrieves all chat IDs in batches.

        Args:
            batch_size: The number of chat IDs to retrieve per batch.

        Yields:
            Batches of chat IDs.

        """
        ...


class LinkRepositoryInterface(ABC):
    """Abstract base class for link repository operations.

    Defines the contract for managing tracked links, including adding,
    removing, listing, and retrieving links.
    """

    @abstractmethod
    async def add_link(
        self,
        chat_id: int,
        url: str,
        tags: List[str],
        filters: List[str],
    ) -> LinkDTO:
        """Adds a new link or updates an existing one.

        Args:
            chat_id: The ID of the chat to which the link belongs.
            url: The URL of the link.
            tags: A list of tag names to associate with the link.
            filters: A list of filters to apply to the link.

        Returns:
            The LinkDTO representing the added or updated link.


        Raises:
            LinkAddError: If the link couldn't be added.

        """
        ...

    @abstractmethod
    async def remove_link(self, chat_id: int, url: str) -> LinkDTO | None:
        """Removes a link.

        Args:
            chat_id: The ID of the chat to which the link belongs.
            url: The URL of the link to remove.

        Returns:
            The LinkDTO representing the removed link, or None if not found.

        """
        ...

    @abstractmethod
    async def list_links(
        self,
        chat_id: int,
    ) -> List[LinkDTO]:
        """Retrieves links for a given chat in batches.

        Args:
            chat_id: The ID of the chat for which to retrieve links.

        Returns:
            List of LinkDTOs.

        """
        ...

    @abstractmethod
    async def get_link(self, chat_id: int, url: str) -> LinkDTO | None:
        """Retrieves a specific link by its URL.

        Args:
            chat_id: The ID of the chat to which the link belongs.
            url: The URL of the link to retrieve.

        Returns:
            The LinkDTO representing the link, or None if not found.

        """
        ...

    @abstractmethod
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

        """
        ...

    @abstractmethod
    async def get_links_by_tag(self, chat_id: int, tag: str) -> List[LinkDTO]:
        """Get all links for a chat with a specific tag.

        Args:
            chat_id: The ID of the chat to get links for.
            tag: The tag to filter links by.

        Returns:
            List[LinkDTO]: A list of all links for the chat with the specified tag.

        """
        ...

    @abstractmethod
    async def update_link_mute_status(self, chat_id: int, url: str, muted: bool) -> bool:
        """Update the mute status for a link.

        Args:
            chat_id: The ID of the chat the link belongs to.
            url: The URL of the link to update.
            muted: The new mute status.

        Returns:
            bool: True if the link was updated, False otherwise.

        """
        ...

    @abstractmethod
    async def get_links_by_tag_and_chat_id(self, chat_id: int, tag_name: str) -> List[LinkDTO]:
        """Get all links for a chat with a specific tag.

        Args:
            chat_id: The ID of the chat to get links for.
            tag_name: The tag to filter links by.

        Returns:
            List[LinkDTO]: A list of all links for the chat with the specified tag.

        """
        ...


class TagRepositoryInterface(ABC):
    """Abstract base class for tag repository operations.

    Defines the contract for managing tags, including retrieving or creating tags.
    """

    @abstractmethod
    async def get_or_create_tag(self, tag_name: str) -> TagDTO:
        """Retrieves a tag by name, or creates a new one if it doesn't exist.

        Args:
            tag_name: The name of the tag.

        Returns:
            The TagDTO instance.

        """
        ...

    @abstractmethod
    async def remove_tag(self, tag_name: str) -> bool:
        """Removes a tag by name.

        Args:
            tag_name: The name of the tag to remove.

        Returns:
            True if the tag was removed, False otherwise.

        """
        ...

    @abstractmethod
    async def get_tag(self, tag_name: str) -> Optional[TagDTO]:
        """Retrieves a tag by name.

        Args:
            tag_name: The name of the tag to retrieve.

        Returns:
            The TagDTO instance, or None if not found.

        """
        ...

    @abstractmethod
    async def get_all_tags(self) -> List[TagDTO]:
        """Retrieves all tags.

        Returns:
            A list of TagDTO instances.

        """
        ...
