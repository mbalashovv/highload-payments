from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from highload_payments.domain.errors import InvalidPaymentTransitionError
from highload_payments.domain.value_objects.money import Money
from highload_payments.domain.value_objects.payment_status import PaymentStatus


@dataclass(slots=True)
class Payment:
    payment_id: UUID
    account_id: UUID
    money: Money
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, payment_id: UUID, account_id: UUID, money: Money) -> "Payment":
        now = datetime.now(tz=UTC)
        return cls(
            payment_id=payment_id,
            account_id=account_id,
            money=money,
            status=PaymentStatus.CREATED,
            created_at=now,
            updated_at=now,
        )

    def mark_processing(self) -> None:
        if self.status is not PaymentStatus.CREATED:
            raise InvalidPaymentTransitionError("processing is allowed only from created")
        self.status = PaymentStatus.PROCESSING
        self.updated_at = datetime.now(tz=UTC)

    def mark_succeeded(self) -> None:
        if self.status not in (PaymentStatus.CREATED, PaymentStatus.PROCESSING):
            raise InvalidPaymentTransitionError("succeeded is not allowed from this state")
        self.status = PaymentStatus.SUCCEEDED
        self.updated_at = datetime.now(tz=UTC)

    def mark_failed(self) -> None:
        if self.status in (PaymentStatus.SUCCEEDED, PaymentStatus.FAILED):
            raise InvalidPaymentTransitionError("failed is not allowed from terminal state")
        self.status = PaymentStatus.FAILED
        self.updated_at = datetime.now(tz=UTC)

