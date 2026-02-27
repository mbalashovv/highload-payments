from highload_payments.application.ports.uow import UnitOfWork
from highload_payments.infrastructure.db.repositories.sqlalchemy_repositories import (
    SqlAlchemyOutboxRepository,
    SqlAlchemyPaymentRepository,
    SqlAlchemyWebhookEndpointRepository,
)


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self.payments = SqlAlchemyPaymentRepository()
        self.outbox = SqlAlchemyOutboxRepository()
        self.webhook_endpoints = SqlAlchemyWebhookEndpointRepository()

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc:
            await self.rollback()

    async def commit(self) -> None:
        raise NotImplementedError

    async def rollback(self) -> None:
        raise NotImplementedError

