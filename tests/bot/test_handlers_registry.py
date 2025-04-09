from src.bot.handlers_registry import HandlersRegistry
from src.handlers.chat_id import chat_id_cmd_handler
from src.handlers.track import track_handler


def test_get_valid_handler() -> None:
    registry = HandlersRegistry()
    # Проверяем, что для известных команд возвращаются корректные обработчики.
    handler = registry.get("/track")
    assert handler is not None
    assert handler == track_handler

    handler = registry.get("/chat_id")
    assert handler is not None
    assert handler == chat_id_cmd_handler


def test_get_invalid_handler() -> None:
    registry = HandlersRegistry()
    # Для неизвестной команды должен возвращаться None.
    handler = registry.get("/nonexistent")
    assert handler is None
