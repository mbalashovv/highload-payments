import orjson

from nats.aio.client import Client as NatsClient

from highload_payments.application.ports.messaging import EventPublisherPort
from highload_payments.domain.entities.outbox_event import OutboxEvent
from highload_payments.infrastructure.settings import NatsConfig


class JetStreamPublisher(EventPublisherPort):
    def __init__(self, nats_config: NatsConfig) -> None:
        self._nats_config = nats_config
        self._client: NatsClient | None = None
        self._jetstream = None

    async def publish(self, event: OutboxEvent) -> None:
        jetstream = await self._get_jetstream()
        payload = {
            "event_id": str(event.event_id),
            "aggregate_id": str(event.aggregate_id),
            "event_type": event.event_type,
            "payload": event.payload,
        }
        data = orjson.dumps(payload, default=str)
        await jetstream.publish(self._nats_config.outbox_subject, payload=data)

    async def _get_jetstream(self):
        if self._jetstream is not None:
            return self._jetstream

        client = NatsClient()
        await client.connect(servers=list(self._nats_config.servers))
        jetstream = client.jetstream()
        await self._ensure_stream(jetstream)

        self._client = client
        self._jetstream = jetstream
        return self._jetstream

    async def _ensure_stream(self, jetstream) -> None:
        try:
            await jetstream.stream_info(self._nats_config.stream_name)
            return
        except Exception:
            pass

        try:
            await jetstream.add_stream(
                name=self._nats_config.stream_name,
                subjects=[self._nats_config.outbox_subject],
            )
        except Exception as exc:
            # Ignore "already exists" race when multiple workers start together.
            if "exists" not in str(exc).lower() and "in use" not in str(exc).lower():
                raise
