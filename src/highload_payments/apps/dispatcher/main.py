import asyncio
import logging
from uuid import UUID

from highload_payments.apps.dispatcher.bootstrap import build_deliver_webhook_use_case
from highload_payments.apps.dispatcher.consumers.webhook_delivery import consume_event
from highload_payments.application.dto.commands import DeliverWebhookCommand
from highload_payments.infrastructure.db.session import create_db_runtime
from highload_payments.infrastructure.messaging.jetstream.webhook_consumer import (
    JetStreamWebhookConsumer,
)
from highload_payments.infrastructure.observability.logging import configure_logging
from highload_payments.infrastructure.settings import load_dispatcher_settings


async def run() -> None:
    settings = load_dispatcher_settings()
    configure_logging(level=settings.common.log_level)
    logger = logging.getLogger(__name__)
    db_runtime = create_db_runtime(settings.db)
    consumer = JetStreamWebhookConsumer(nats_config=settings.nats)

    try:
        use_case = build_deliver_webhook_use_case(
            settings=settings,
            session_factory=db_runtime.session_factory,
        )

        async def handle_envelope(envelope: dict) -> None:
            payload = envelope.get("payload")
            if not isinstance(payload, dict):
                logger.warning("skipping message with invalid payload format")
                return

            command = DeliverWebhookCommand(
                event_id=UUID(str(envelope["event_id"])),
                payment_id=UUID(str(payload["payment_id"])),
                account_id=UUID(str(payload["account_id"])),
                event_type=str(envelope["event_type"]),
                payload=payload,
            )
            delivered = await consume_event(use_case, command)
            logger.info(
                "dispatcher delivered webhook event=%s to endpoints=%s",
                command.event_id,
                delivered,
            )

        await consumer.run(
            handle_envelope,
            poll_interval_seconds=settings.dispatcher.poll_interval_seconds,
        )
    finally:
        await consumer.close()
        await db_runtime.dispose()


if __name__ == "__main__":
    asyncio.run(run())
