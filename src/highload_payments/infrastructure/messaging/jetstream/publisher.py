from highload_payments.application.ports.messaging import EventPublisherPort
from highload_payments.domain.entities.outbox_event import OutboxEvent
from highload_payments.infrastructure.settings import NatsConfig


class JetStreamPublisher(EventPublisherPort):
    def __init__(self, nats_config: NatsConfig) -> None:
        self._nats_config = nats_config

    async def publish(self, event: OutboxEvent) -> None:
        raise NotImplementedError
