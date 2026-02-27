from typing import Protocol
from uuid import UUID

from highload_payments.domain.entities.outbox_event import OutboxEvent
from highload_payments.domain.entities.payment import Payment
from highload_payments.domain.entities.webhook_endpoint import WebhookEndpoint


class PaymentRepository(Protocol):
    async def add(self, payment: Payment) -> None: ...

    async def get(self, payment_id: UUID) -> Payment | None: ...


class OutboxRepository(Protocol):
    async def add(self, event: OutboxEvent) -> None: ...

    async def claim_batch(self, size: int) -> list[OutboxEvent]: ...

    async def update(self, event: OutboxEvent) -> None: ...


class WebhookEndpointRepository(Protocol):
    async def get_by_account(self, account_id: UUID) -> list[WebhookEndpoint]: ...

