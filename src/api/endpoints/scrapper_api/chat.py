import logging

from fastapi import APIRouter, Depends, HTTPException

from src.db.repositories.base import ChatRepositoryInterface
from src.dependencies import get_chat_repo
from src.scrapper.schemas import ChatResponse

chat_router = APIRouter()
logger = logging.getLogger(__name__)


@chat_router.post("/tg-chat/{tg_id}", response_model=ChatResponse)
async def register_chat(
    tg_id: int,
    chat_repo: ChatRepositoryInterface = Depends(get_chat_repo),
) -> ChatResponse:
    """Registers a chat by its ID.
    If the chat is already registered, returns a notification.

    Args:
        tg_id (int): The ID of the chat to register.
        chat_repo: The chat repository dependency.

    Returns:
        ChatResponse: The response indicating the result of the registration.

    """
    logger.info("Attempting to register chat with ID: %s", tg_id)

    existing_chat = await chat_repo.get_chat(tg_id)
    if existing_chat is not None:
        logger.info("Chat with ID %s is already registered", tg_id)
        return ChatResponse(tg_id=tg_id, message="Chat is already registered")

    await chat_repo.register(tg_id)
    logger.info("Chat with ID %s has been successfully registered", tg_id)
    return ChatResponse(tg_id=tg_id, message="Chat registered")


@chat_router.delete("/tg-chat/{tg_id}", response_model=ChatResponse)
async def delete_chat(
    tg_id: int,
    chat_repo: ChatRepositoryInterface = Depends(get_chat_repo),
) -> ChatResponse:
    """Deletes a chat by its ID.
    If the chat is not found, returns a 404 error.

    Args:
        tg_id (int): The ID of the chat to delete.
        chat_repo: The chat repository dependency.

    Returns:
        ChatResponse: The response indicating the result of the deletion.

    Raises:
        HTTPException: If the chat does not exist.

    """
    logger.info("Attempting to delete chat with ID: %s", tg_id)
    if not await chat_repo.get_chat(tg_id):
        logger.error("Chat with ID %s not found", tg_id)
        raise HTTPException(status_code=404, detail="Chat does not exist")

    await chat_repo.delete_chat(tg_id)
    logger.info("Chat with ID %s has been successfully deleted", tg_id)
    return ChatResponse(tg_id=tg_id, message="Chat successfully deleted")
