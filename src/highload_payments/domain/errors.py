class DomainError(Exception):
    """Base error for domain rule violations."""


class InvalidPaymentTransitionError(DomainError):
    """Raised when a payment status transition is not allowed."""

