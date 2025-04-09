import logging

from telethon import events

from src.bot.command_context import CommandContext

logger = logging.getLogger(__name__)


async def mute_tag_handler(event: events.NewMessage.Event, context: CommandContext) -> None:
    """Handles the /mute_tag command.

    This command mutes a specified tag for a chat, preventing notifications
    related to that tag.

    Args:
        event: The Telegram message event.
        context: The command execution context.

    """
    chat_id = event.chat_id

    command_parts = event.text.split(maxsplit=1)

    correct_parts_count = 2
    if len(command_parts) < correct_parts_count:
        await event.reply("Please specify the tag name. For example: /mute python")
        return

    tag_name = command_parts[1].strip()

    try:
        scrapper_client = context.scrapper_client
        response = await scrapper_client.mute_tag(chat_id, tag_name)

        if response.get("affected_links", 0) > 0:
            await event.reply(
                f"Tag '{tag_name}' has been muted.\n \
                    Affected links: {response.get('affected_links', 0)}",
            )
        else:
            await event.reply(f"No links found with the tag '{tag_name}'")

    except Exception as e:
        logger.exception("Error muting tag", extra={"chat_id": chat_id, "tag": tag_name})
        await event.reply(f"An error occurred while muting the tag: {e!s}")


async def unmute_tag_handler(event: events.NewMessage.Event, context: CommandContext) -> None:
    """Handles the /unmute_tag command.

    This command unmutes a specified tag for a chat, allowing notifications
    related to that tag to be received again.

    Args:
        event: The Telegram message event.
        context: The command execution context.

    """
    chat_id = event.chat_id

    command_parts = event.text.split(maxsplit=1)

    correct_parts_count = 2
    if len(command_parts) < correct_parts_count:
        await event.reply("Please specify the tag name. For example: /unmute  python")
        return

    tag_name = command_parts[1].strip()

    try:
        scrapper_client = context.scrapper_client
        response = await scrapper_client.unmute_tag(chat_id, tag_name)

        if response.get("affected_links", 0) > 0:
            await event.reply(
                f"Tag '{tag_name}' has been unmuted.\n \
                    Affected links: {response.get('affected_links', 0)}",
            )
        else:
            await event.reply(f"No links found with the tag '{tag_name}'")

    except Exception as e:
        logger.exception("Error unmuting tag", extra={"chat_id": chat_id, "tag": tag_name})
        await event.reply(f"An error occurred while unmuting the tag: {e!s}")
