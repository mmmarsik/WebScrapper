import logging

from fastapi import APIRouter, Depends, Header, HTTPException

from src.db.repositories.base import ChatRepositoryInterface, LinkRepositoryInterface
from src.dependencies import get_chat_repo, get_link_repo
from src.http_constants import HTTPStatus
from src.scrapper.schemas import TagMuteRequest, TagMuteResponse

tag_router = APIRouter()
logger = logging.getLogger(__name__)


@tag_router.post(
    "/tags/mute",
    status_code=200,
    summary="Mute a tag",
    response_description="Tag muted",
    response_model=TagMuteResponse,
)
async def mute_tag(
    request: TagMuteRequest,
    chat_id: int = Header(..., alias="Tg-Chat-Id"),
    chat_repo: ChatRepositoryInterface = Depends(get_chat_repo),
    link_repo: LinkRepositoryInterface = Depends(get_link_repo),
) -> TagMuteResponse:
    """Mutes a tag for a specific chat.

    Args:
        request: The request containing the tag name to mute.
        chat_id: The ID of the chat.
        chat_repo: The chat repository.
        link_repo: The link repository.

    Returns:
        TagMuteResponse: Information about the muted tag.

    Raises:
        HTTPException: If the chat is not registered or the tag is not found.

    """
    logger.info("Attempting to mute tag for chat ID: %s", chat_id)

    if not await chat_repo.get_chat(chat_id):
        logger.error("Chat with ID %s is not registered", chat_id)
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST.value,
            detail="Please register the chat first",
        )

    try:
        links = await link_repo.get_links_by_tag(chat_id, request.tag_name)
    except Exception as e:
        logger.exception("Database error while fetching links for chat ID: %s", chat_id)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            detail="Internal server error occurred while fetching links",
        ) from e

    if not links:
        logger.warning("No links found with tag '%s' for chat ID %s", request.tag_name, chat_id)
        return TagMuteResponse(tag_name=request.tag_name, muted=True, affected_links=0)

    affected_count = 0
    try:
        for link in links:
            updated = await link_repo.update_link_mute_status(chat_id, str(link.url), True)
            if updated:
                affected_count += 1
    except Exception as e:
        logger.exception(
            "Error updating mute status for link %s in chat ID: %s",
            link.url,
            chat_id,
        )
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            detail="Internal server error occurred while updating link mute status",
        ) from e

    logger.info(
        "Successfully muted tag for chat ID: %s; affected links: %s",
        chat_id,
        affected_count,
    )
    return TagMuteResponse(tag_name=request.tag_name, muted=True, affected_links=affected_count)


@tag_router.post(
    "/tags/unmute",
    status_code=200,
    summary="Unmute a tag",
    response_description="Tag unmuted",
    response_model=TagMuteResponse,
)
async def unmute_tag(
    request: TagMuteRequest,
    chat_id: int = Header(..., alias="Tg-Chat-Id"),
    chat_repo: ChatRepositoryInterface = Depends(get_chat_repo),
    link_repo: LinkRepositoryInterface = Depends(get_link_repo),
) -> TagMuteResponse:
    """Unmutes a tag for a specific chat.

    Args:
        request: The request containing the tag name to unmute.
        chat_id: The ID of the chat.
        chat_repo: The chat repository.
        link_repo: The link repository.

    Returns:
        TagMuteResponse: Information about the unmuted tag.

    Raises:
        HTTPException: If the chat is not registered or the tag is not found.

    """
    logger.info("Attempting to unmute tag for chat ID: %s", chat_id)

    if not await chat_repo.get_chat(chat_id):
        logger.error("Chat with ID %s is not registered", chat_id)
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST.value,
            detail="Please register the chat first",
        )

    try:
        links = await link_repo.get_links_by_tag(chat_id, request.tag_name)
    except Exception as e:
        logger.exception("Database error while fetching links for chat ID: %s", chat_id)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            detail="Internal server error occurred while fetching links",
        ) from e

    if not links:
        logger.warning("No links found with tag '%s' for chat ID %s", request.tag_name, chat_id)
        return TagMuteResponse(tag_name=request.tag_name, muted=False, affected_links=0)

    affected_count = 0
    try:
        for link in links:
            updated = await link_repo.update_link_mute_status(chat_id, str(link.url), False)
            if updated:
                affected_count += 1
    except Exception as e:
        logger.exception(
            "Error updating unmute status for link %s in chat ID: %s",
            link.url,
            chat_id,
        )
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            detail="Internal server error occurred while updating link unmute status",
        ) from e

    logger.info(
        "Successfully unmuted tag for chat ID: %s; affected links: %s",
        chat_id,
        affected_count,
    )
    return TagMuteResponse(tag_name=request.tag_name, muted=False, affected_links=affected_count)
