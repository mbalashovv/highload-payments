from typing import Protocol

from highload_payments.application.ports.repositories import (
    OutboxRepository,
    PaymentRepository,
    WebhookEndpointRepository,
)


class UnitOfWork(Protocol):
    payments: PaymentRepository
    outbox: OutboxRepository
    webhook_endpoints: WebhookEndpointRepository

    async def __aenter__(self) -> "UnitOfWork": ...

    async def __aexit__(self, exc_type, exc, tb) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

