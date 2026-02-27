class ApplicationError(Exception):
    """Base error for use-case failures."""


class NotFoundError(ApplicationError):
    """Raised when requested entity does not exist."""

