from uuid import UUID

from highload_payments.application.ports.repositories import PaymentRepository
from highload_payments.domain.entities.payment import Payment
from highload_payments.infrastructure.db.repositories.base import SqlAlchemyRepository


class SqlAlchemyPaymentRepository(SqlAlchemyRepository, PaymentRepository):
    async def add(self, payment: Payment) -> None:
        raise NotImplementedError

    async def get(self, payment_id: UUID) -> Payment | None:
        raise NotImplementedError
