from typing import List

from pydantic import AnyUrl, BaseModel, Field


class ChatResponse(BaseModel):
    """Response schema for chat registration and deletion endpoints."""

    tg_id: int
    message: str


class ApiErrorResponse(BaseModel):
    """Schema for API error response."""

    description: str
    code: str
    exception_name: str = Field(..., alias="exceptionName")
    exception_message: str = Field(..., alias="exceptionMessage")
    stacktrace: List[str]


class LinkResponse(BaseModel):
    """Response schema for link-related operations."""

    tg_id: int = Field(..., alias="chat_id")
    url: AnyUrl
    tags: List[str]
    filters: List[str]
    muted: bool = False


class AddLinkRequest(BaseModel):
    """Schema for adding a tracked link."""

    link: AnyUrl
    tags: List[str]
    filters: List[str]


class RemoveLinkRequest(BaseModel):
    """Schema for removing a tracked link."""

    link: AnyUrl


class ListLinksResponse(BaseModel):
    """Schema for retrieving a list of tracked links."""

    links: List[LinkResponse]
    size: int


class LinkUpdate(BaseModel):
    """Schema for sending link updates to the bot API."""

    id: int = Field(..., description="Unique identifier for the update")
    url: AnyUrl = Field(..., description="URL of the updated link")
    description: str = Field(..., description="Description of the update")
    tg_chat_ids: List[int] = Field(
        ...,
        alias="tgChatIds",
        description="List of Telegram chat IDs to notify",
    )

    class Config:
        allow_population_by_field_name = True


class AddLinkResponse(BaseModel):
    """Response schema for adding a link."""

    url: str
    tags: List[str]
    filters: List[str]
    muted: bool = False


class RemoveLinkResponse(BaseModel):
    """Response schema for removing a link."""

    success: bool


class TagMuteRequest(BaseModel):
    """Schema for muting/unmuting a tag."""

    tag_name: str = Field(..., description="Name of the tag to mute/unmute")


class TagMuteResponse(BaseModel):
    """Response schema for muting/unmuting a tag."""

    tag_name: str
    muted: bool
    affected_links: int
