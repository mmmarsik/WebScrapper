import logging

from fastapi import APIRouter, Depends, Header, HTTPException

from src.api.utils.link_conversion import convert_link_dto_to_response
from src.db.repositories.base import (
    ChatRepositoryInterface,
    LinkAddError,
    LinkRepositoryInterface,
)
from src.dependencies import get_chat_repo, get_link_repo
from src.http_constants import HTTPStatus
from src.scrapper.schemas import AddLinkRequest, LinkResponse, ListLinksResponse, RemoveLinkRequest

logger = logging.getLogger(__name__)

link_router = APIRouter()


@link_router.get("/links", response_model=ListLinksResponse)
async def get_links(
    tg_chat_id: int = Header(..., alias="Tg-Chat-Id"),
    chat_repo: ChatRepositoryInterface = Depends(get_chat_repo),
    link_repo: LinkRepositoryInterface = Depends(get_link_repo),
) -> ListLinksResponse:
    """Retrieves all tracked links for a chat.
    Requires the chat to be registered.

    Args:
        tg_chat_id (int): The ID of the Telegram chat, provided in the header.
        chat_repo: The chat repository dependency.
        link_repo: The link repository dependency.

    Returns:
        ListLinksResponse: A response containing the list of tracked links and their count.

    Raises:
        HTTPException: If the chat is not registered.

    """
    logger.info("Listing links for chat ID: %s", tg_chat_id)

    if not await chat_repo.get_chat(tg_chat_id):
        logger.error("Chat with ID %s is not registered", tg_chat_id)
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST.value,
            detail="Please register the chat first",
        )

    try:
        links = await link_repo.list_links(chat_id=tg_chat_id)
    except Exception as e:
        logger.exception("Database error while listing links for chat ID %s", tg_chat_id)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            detail="Internal server error occurred while listing links",
        ) from e

    links_list = [convert_link_dto_to_response(link) for link in links]
    return ListLinksResponse(links=links_list, size=len(links_list))


@link_router.post("/links", response_model=LinkResponse)
async def add_link(
    add_req: AddLinkRequest,
    tg_chat_id: int = Header(..., alias="Tg-Chat-Id"),
    chat_repo: ChatRepositoryInterface = Depends(get_chat_repo),
    link_repo: LinkRepositoryInterface = Depends(get_link_repo),
) -> LinkResponse:
    """Adds a tracked link for a chat.
    Requires the chat to be registered.

    Args:
        add_req (AddLinkRequest): The request containing the link, tags, and filters.
        tg_chat_id (int): The ID of the Telegram chat, provided in the header.
        chat_repo: The chat repository dependency.
        link_repo: The link repository dependency.

    Returns:
        LinkResponse: A response containing the details of the added link.

    Raises:
        HTTPException: If the chat is not registered or link adding failed.

    """
    logger.info("Attempting to add link for chat ID: %s", tg_chat_id)
    if not await chat_repo.get_chat(tg_chat_id):
        logger.exception("Chat with ID %s is not registered", tg_chat_id)
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST.value,
            detail="Please register the chat first",
        )

    try:
        link_data = await link_repo.add_link(
            tg_chat_id,
            str(add_req.link),
            add_req.tags,
            add_req.filters,
        )
        logger.info("Successfully added link for chat ID: %s", tg_chat_id)

        return convert_link_dto_to_response(link_data)
    except LinkAddError as e:
        logger.exception("Failed to add link for chat ID: %s", tg_chat_id)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            detail=str(e),
        ) from e


@link_router.delete("/links", response_model=LinkResponse)
async def delete_link(
    remove_req: RemoveLinkRequest,
    tg_chat_id: int = Header(..., alias="Tg-Chat-Id"),
    chat_repo: ChatRepositoryInterface = Depends(get_chat_repo),
    link_repo: LinkRepositoryInterface = Depends(get_link_repo),
) -> LinkResponse:
    """Removes a tracked link for a chat.
    If the link is not found, returns a 404 error.

    Args:
        remove_req (RemoveLinkRequest): The request containing the link to remove.
        tg_chat_id (int): The ID of the Telegram chat, provided in the header.
        chat_repo: The chat repository dependency.
        link_repo: The link repository dependency.

    Returns:
        LinkResponse: A response containing the details of the removed link.

    Raises:
        HTTPException: If the chat is not registered or the link is not found.

    """
    logger.info("Attempting to remove link for chat ID: %s", tg_chat_id)
    if not await chat_repo.get_chat(tg_chat_id):
        logger.exception("Chat with ID %s is not registered", tg_chat_id)
        raise HTTPException(status_code=400, detail="Please register the chat first")

    existing = await link_repo.get_link(tg_chat_id, str(remove_req.link))
    if not existing:
        logger.error("Link not found for chat ID: %s", tg_chat_id)
        raise HTTPException(status_code=404, detail="Link not found")

    removed = await link_repo.remove_link(tg_chat_id, str(remove_req.link))
    if removed is None:
        raise HTTPException(status_code=500, detail="Link removal failed")
    logger.info("Successfully removed link for chat ID: %s", tg_chat_id)
    return convert_link_dto_to_response(removed)
