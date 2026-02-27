from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PaymentCreatedEvent:
    event_id: UUID
    payment_id: UUID
    account_id: UUID
    amount_minor: int
    currency: str

