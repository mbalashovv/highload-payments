from dataclasses import dataclass
from uuid import UUID

from highload_payments.domain.value_objects.payment_status import PaymentStatus


@dataclass(frozen=True, slots=True)
class PaymentResult:
    payment_id: UUID
    status: PaymentStatus
    duplicated: bool

