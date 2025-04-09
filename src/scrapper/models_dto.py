from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from pydantic import BaseModel, StringConstraints


class TagDTO(BaseModel):
    """Represents a tag.

    Attributes:
        tag_name: The name of the tag.

    """

    tag_name: Annotated[str, StringConstraints(min_length=1, max_length=50)]


class UserDTO(BaseModel):
    """Represents a user.

    Attributes:
        user_id: The ID of the user.
        username: The username of the user.

    """

    user_id: int
    username: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts the User instance to a dictionary."""
        return self.model_dump()


class LinkDTO(BaseModel):
    """Represents a link.

    Attributes:
        chat_id: The ID of the chat the link belongs to.
        url: The URL of the link.
        last_updated: The last time the link was updated.
        tags: The tags associated with the link.
        filters: The filters associated with the link.
        muted: Whether the link is muted.

    """

    chat_id: int
    url: Annotated[str, StringConstraints(min_length=1, max_length=255)]
    last_updated: Optional[datetime] = None
    tags: List[TagDTO]
    filters: List[str]
    muted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Link instance to a dictionary."""
        return self.model_dump()
