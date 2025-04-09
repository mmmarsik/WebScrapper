import logging
from typing import Dict


class SessionManager:
    """Manages active dialog sessions.
    Allows adding, checking, and removing a session for a specific user.
    This helps separate state logic from handlers, making the system more testable.
    """

    def __init__(self) -> None:
        """Initializes the session manager with an empty session dictionary."""
        self._sessions: Dict[int, str] = {}
        self._logger = logging.getLogger(__name__)

    def has_session(self, user_id: int) -> bool:
        """Checks if there is an active session for the given user ID.

        Args:
            user_id (int): The ID of the user.

        Returns:
            bool: True if a session exists, False otherwise.

        """
        return user_id in self._sessions

    def add_session(self, user_id: int, session_type: str) -> None:
        """Registers a new session for the user.

        Args:
            user_id (int): The ID of the user.
            session_type (str): The type of session being started.

        """
        self._sessions[user_id] = session_type
        self._logger.info("Session started for user %s with type '%s'", user_id, session_type)

    def remove_session(self, user_id: int) -> None:
        """Removes the session for the given user ID if it exists.

        Args:
            user_id (int): The ID of the user.

        """
        if user_id in self._sessions:
            del self._sessions[user_id]
            self._logger.info("Session removed for user %s", user_id)
