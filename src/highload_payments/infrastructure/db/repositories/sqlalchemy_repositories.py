from uuid import UUID

from highload_payments.application.ports.repositories import (
    OutboxRepository,
    PaymentRepository,
    WebhookEndpointRepository,
)
from highload_payments.domain.entities.outbox_event import OutboxEvent
from highload_payments.domain.entities.payment import Payment
from highload_payments.domain.entities.webhook_endpoint import WebhookEndpoint


class SqlAlchemyPaymentRepository(PaymentRepository):
    async def add(self, payment: Payment) -> None:
        raise NotImplementedError

    async def get(self, payment_id: UUID) -> Payment | None:
        raise NotImplementedError


class SqlAlchemyOutboxRepository(OutboxRepository):
    async def add(self, event: OutboxEvent) -> None:
        raise NotImplementedError

    async def claim_batch(self, size: int) -> list[OutboxEvent]:
        raise NotImplementedError

    async def update(self, event: OutboxEvent) -> None:
        raise NotImplementedError


class SqlAlchemyWebhookEndpointRepository(WebhookEndpointRepository):
    async def get_by_account(self, account_id: UUID) -> list[WebhookEndpoint]:
        raise NotImplementedError

