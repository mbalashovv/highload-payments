import asyncio
import logging
from uuid import UUID

from highload_payments.apps.dispatcher.bootstrap import build_deliver_webhook_use_case
from highload_payments.apps.dispatcher.consumers.webhook_delivery import consume_event
from highload_payments.application.policies.retry import ExponentialBackoffPolicy
from highload_payments.application.dto.commands import DeliverWebhookCommand
from highload_payments.infrastructure.db.session import create_db_runtime
from highload_payments.infrastructure.messaging.jetstream.webhook_consumer import (
    ConsumeDecision,
    JetStreamWebhookConsumer,
)
from highload_payments.infrastructure.observability.logging import configure_logging
from highload_payments.infrastructure.settings import load_dispatcher_settings


async def run() -> None:
    settings = load_dispatcher_settings()
    configure_logging(level=settings.common.log_level)
    logger = logging.getLogger(__name__)
    db_runtime = create_db_runtime(settings.db)
    max_attempts = settings.dispatcher.max_retries + 1
    backoff_policy = ExponentialBackoffPolicy(
        base_seconds=settings.dispatcher.retry_base_seconds,
        max_seconds=settings.dispatcher.retry_max_seconds,
        jitter_seconds=settings.dispatcher.retry_jitter_seconds,
    )
    consumer = JetStreamWebhookConsumer(
        nats_config=settings.nats,
        max_deliver=max_attempts,
        ack_wait_seconds=settings.dispatcher.consumer_ack_wait_seconds,
    )

    try:
        use_case = build_deliver_webhook_use_case(
            settings=settings,
            session_factory=db_runtime.session_factory,
        )

        async def handle_envelope(envelope: dict, delivery_attempt: int) -> ConsumeDecision:
            payload = envelope.get("payload")
            if not isinstance(payload, dict):
                logger.warning("skipping message with invalid payload format")
                return ConsumeDecision.term()

            command = DeliverWebhookCommand(
                event_id=UUID(str(envelope["event_id"])),
                payment_id=UUID(str(payload["payment_id"])),
                account_id=UUID(str(payload["account_id"])),
                event_type=str(envelope["event_type"]),
                payload=payload,
            )
            outcome = await consume_event(use_case, command)
            logger.info(
                "dispatcher processed webhook event=%s delivered=%s retryable_failures=%s non_retryable_failures=%s attempt=%s",
                command.event_id,
                outcome.delivered_count,
                outcome.retryable_failures,
                outcome.non_retryable_failures,
                delivery_attempt,
            )
            if outcome.should_retry and delivery_attempt < max_attempts:
                delay = backoff_policy.next_delay(delivery_attempt)
                return ConsumeDecision.nak(delay_seconds=delay)
            if outcome.should_retry:
                logger.warning(
                    "marking webhook event terminal after max attempts: event=%s attempts=%s",
                    command.event_id,
                    delivery_attempt,
                )
                return ConsumeDecision.term()
            return ConsumeDecision.ack()

        await consumer.run(
            handle_envelope,
            poll_interval_seconds=settings.dispatcher.poll_interval_seconds,
        )
    finally:
        await consumer.close()
        await db_runtime.dispose()


if __name__ == "__main__":
    asyncio.run(run())
