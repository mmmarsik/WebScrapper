from enum import StrEnum


class ErrorMessage(StrEnum):
    """Error messages."""

    LINK_NOT_FOUND = "🔍 Link not found in your tracking list"
    CHAT_NOT_REGISTERED = "🚨 Chat not registered! Use /start to register"
    INVALID_TRACK_COMMAND_USAGE = "❌ Usage: /track(or /untrack) <URL>"
    INVALID_MUTE_COMMAND_USAGE = "❌ Usage: /mute(or /unmute) <tag>"
    ERROR_EXPECTED_TEXT_NOT_COMMAND = "❌ Expected text, not command"
    UNKNOWN_URL = "❌ Unknown URL"
    NETWORK = "Network error. Please check your connection and try again."
    EMPTY_LIST = "📭 Tracked links list is empty"
    ERROR_ADDING_LINK = "❌ Error adding link. Check URL format:\nhttps://example.com/"
    ERROR_GETTING_LINKS = "⚠️ BOT ERROR: while getting links list. Try again later."
    ERROR_REMOVING_LINK = "⚠️ BOT ERROR: while removing link. Try again later."
    ERROR_GETTING_CHAT_ID = "⚠️ BOT ERROR: while getting Chat ID. Try again later."
    ERROR_PROCESSING_LIST_LINKS = "⚠️ BOT ERROR: while processing list links. Try again later."
    ERROR_PROCESSING_TRACK = "⚠️ BOT ERROR: while processing track. Try again later."
    ERROR_PROCESSING_START = "⚠️ BOT ERROR: while processing start. Try again later."
    ERROR_PROCESSING_HELP = "⚠️ BOT ERROR: while processing help. Try again later."
    ERROR_PROCESSING_CHAT_ID = "⚠️ BOT ERROR: while processing chat tg_id. Try again later."
    ERROR_PROCESSING_UNTRACK = "⚠️ BOT ERROR: while processing untrack. Try again later."
    ERROR_PROCESSING_MUTE = "⚠️ BOT ERROR: while processing mute. Try again later."
    ERROR_PROCESSING_UNMUTE = "⚠️ BOT ERROR: while processing unmute. Try again later."
