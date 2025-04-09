class StackOverflowClientError(Exception):
    """Base class for Stack Overflow client errors.

    This exception serves as a parent class for more specific exceptions
    that may occur during interactions with the Stack Overflow API.
    """


class StackOverflowQuestionNotFoundError(StackOverflowClientError):
    """Exception raised when a requested Stack Overflow question is not found.

    This exception is raised when the Stack Overflow API returns an error
    indicating that the specified question does not exist.
    """
