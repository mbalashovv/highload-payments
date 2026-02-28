from uuid import UUID

from highload_payments.domain.value_objects.money import Money
from highload_payments.domain.value_objects.payment_status import PaymentStatus
from highload_payments.application.ports.repositories import PaymentRepository
from highload_payments.domain.entities.payment import Payment
from highload_payments.infrastructure.db.models.payment import PaymentModel
from highload_payments.infrastructure.db.repositories.base import SqlAlchemyRepository


class SqlAlchemyPaymentRepository(SqlAlchemyRepository, PaymentRepository):
    async def add(self, payment: Payment) -> None:
        self._session.add(
            PaymentModel(
                payment_id=payment.payment_id,
                account_id=payment.account_id,
                amount_minor=payment.money.amount_minor,
                currency=payment.money.currency,
                status=payment.status.value,
                created_at=payment.created_at,
                updated_at=payment.updated_at,
            )
        )

    async def get(self, payment_id: UUID) -> Payment | None:
        row = await self._session.get(PaymentModel, payment_id)
        if row is None:
            return None
        return Payment(
            payment_id=row.payment_id,
            account_id=row.account_id,
            money=Money(amount_minor=row.amount_minor, currency=row.currency),
            status=PaymentStatus(row.status),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
