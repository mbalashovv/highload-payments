from enum import StrEnum


class WebhookDeliveryStatus(StrEnum):
    PENDING = "pending"
    RETRY = "retry"
    SUCCEEDED = "succeeded"
    FAILED_TERMINAL = "failed_terminal"
