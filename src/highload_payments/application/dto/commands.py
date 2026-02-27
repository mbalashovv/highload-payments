from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CreatePaymentCommand:
    account_id: UUID
    amount_minor: int
    currency: str
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class DeliverWebhookCommand:
    event_id: UUID
    payment_id: UUID
    account_id: UUID
    event_type: str
    payload: dict

