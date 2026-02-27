from highload_payments.application.ports.messaging import EventPublisherPort
from highload_payments.domain.entities.outbox_event import OutboxEvent


class JetStreamPublisher(EventPublisherPort):
    async def publish(self, event: OutboxEvent) -> None:
        raise NotImplementedError

