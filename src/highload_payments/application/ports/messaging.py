from typing import Protocol

from highload_payments.domain.entities.outbox_event import OutboxEvent


class EventPublisherPort(Protocol):
    async def publish(self, event: OutboxEvent) -> None: ...

