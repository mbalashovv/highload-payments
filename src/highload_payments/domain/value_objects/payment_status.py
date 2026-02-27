from enum import StrEnum


class PaymentStatus(StrEnum):
    CREATED = "created"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

