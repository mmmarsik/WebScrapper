import logging

from telethon import events

from src.bot.command_context import CommandContext
from src.handlers.handler_utils import ErrorMessage
from src.http_constants import HTTPStatus
from src.scrapper.scrapper_exceptions import (
    ScrapperAPIError,
    ScrapperAPIHTTPError,
    ScrapperAPIRequestError,
)

logger = logging.getLogger(__name__)


async def list_links_handler(event: events.NewMessage.Event, context: CommandContext) -> None:
    """Handler for /list command.
    Retrieves tracked links via GET /links and formats the output.

    Args:
        event (events.NewMessage.Event): Telegram new message event
        context (CommandContext): Command execution context

    """
    user_id = event.sender_id
    try:
        logger.info("Listing links for user %s", user_id)
        response = await context.scrapper_client.list_links(user_id)
        links = response.get("links", [])

        logger.info("Links: %s", links)

        if not links:
            await event.reply(ErrorMessage.EMPTY_LIST)
            return

        formatted_links = []
        for idx, link in enumerate(links, 1):
            url = link.get("url", ErrorMessage.UNKNOWN_URL)
            tags = link.get("tags", [])
            tags_str = f" | Tags: {', '.join(tags)}" if tags else ""
            formatted_links.append(f"{idx}. 🌐 {url}{tags_str}")

        response_text = "📋 Tracked links:\n\n" + "\n\n".join(formatted_links)
        await event.reply(response_text)

    except ScrapperAPIHTTPError as e:
        logger.exception("List links error for user %s", user_id)
        if e.status_code == HTTPStatus.BAD_REQUEST.value:
            await event.reply(ErrorMessage.CHAT_NOT_REGISTERED)
        else:
            await event.reply(ErrorMessage.ERROR_GETTING_LINKS)
    except ScrapperAPIRequestError:
        logger.exception("Network error listing links for user %s", user_id)
        await event.reply("Network error. Please check your connection and try again.")
    except (ScrapperAPIError, Exception):
        logger.exception("Unexpected error listing links for user %s", user_id)
        await event.reply(ErrorMessage.ERROR_GETTING_LINKS)
