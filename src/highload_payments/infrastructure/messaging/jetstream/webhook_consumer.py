import asyncio
import orjson
import logging
from collections.abc import Awaitable, Callable

import nats.errors
from nats.aio.client import Client as NatsClient
from nats.js.errors import FetchTimeoutError

from highload_payments.infrastructure.settings import NatsConfig


class JetStreamWebhookConsumer:
    def __init__(
        self,
        nats_config: NatsConfig,
        batch_size: int = 64,
        fetch_timeout_seconds: float = 1.0,
    ) -> None:
        self._nats_config = nats_config
        self._batch_size = batch_size
        self._fetch_timeout_seconds = fetch_timeout_seconds
        self._client: NatsClient | None = None
        self._subscription = None
        self._logger = logging.getLogger(__name__)

    async def run(
        self,
        handler: Callable[[dict], Awaitable[None]],
        poll_interval_seconds: float,
    ) -> None:
        subscription = await self._get_subscription()
        while True:
            try:
                messages = await subscription.fetch(
                    batch=self._batch_size,
                    timeout=self._fetch_timeout_seconds,
                )
            except (nats.errors.TimeoutError, FetchTimeoutError):
                await asyncio.sleep(poll_interval_seconds)
                continue

            for message in messages:
                try:
                    envelope = orjson.loads(message.data.decode("utf-8"))
                    await handler(envelope)
                except Exception:
                    self._logger.exception("failed to process jetstream message")
                    await message.nak()
                else:
                    await message.ack()

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.close()
        self._client = None
        self._subscription = None

    async def _get_subscription(self):
        if self._subscription is not None:
            return self._subscription

        client = NatsClient()
        await client.connect(servers=list(self._nats_config.servers))
        jetstream = client.jetstream()
        await self._ensure_stream(jetstream)

        subscription = await jetstream.pull_subscribe(
            subject=self._nats_config.outbox_subject,
            durable=self._nats_config.consumer_durable,
            stream=self._nats_config.stream_name,
        )

        self._client = client
        self._subscription = subscription
        return self._subscription

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
            if "exists" not in str(exc).lower() and "in use" not in str(exc).lower():
                raise
