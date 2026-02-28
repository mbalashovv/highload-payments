from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from highload_payments.application.ports.uow import UnitOfWork
from highload_payments.infrastructure.db.repositories import (
    SqlAlchemyOutboxRepository,
    SqlAlchemyPaymentRepository,
    SqlAlchemyWebhookEndpointRepository,
)


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self.payments: SqlAlchemyPaymentRepository
        self.outbox: SqlAlchemyOutboxRepository
        self.webhook_endpoints: SqlAlchemyWebhookEndpointRepository

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_factory()
        self.payments = SqlAlchemyPaymentRepository(self._session)
        self.outbox = SqlAlchemyOutboxRepository(self._session)
        self.webhook_endpoints = SqlAlchemyWebhookEndpointRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: Any,
    ) -> None:
        if exc:
            await self.rollback()
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("UnitOfWork session is not initialized")
        await self._session.commit()

    async def rollback(self) -> None:
        if self._session is None:
            return
        await self._session.rollback()
