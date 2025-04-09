class GitHubClientError(Exception):
    """Base class for GitHub client errors.

    This exception serves as a parent class for more specific exceptions
    that may occur during interactions with the GitHub API.
    """


class GitHubRepoNotFoundError(GitHubClientError):
    """Exception raised when a requested GitHub repository is not found.

    This exception is raised when the GitHub API returns an error indicating
    that the specified repository does not exist.
    """
