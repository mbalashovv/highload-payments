from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from highload_payments.application.policies.retry import ExponentialBackoffPolicy
from highload_payments.application.use_cases.deliver_webhook_event import (
    DeliverWebhookEventUseCase,
)
from highload_payments.infrastructure.db.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork
from highload_payments.infrastructure.delivery.webhook.http_sender import HttpWebhookSender
from highload_payments.infrastructure.settings import DispatcherSettings


def build_deliver_webhook_use_case(
    settings: DispatcherSettings,
    session_factory: async_sessionmaker[AsyncSession],
) -> DeliverWebhookEventUseCase:
    return DeliverWebhookEventUseCase(
        uow=SqlAlchemyUnitOfWork(session_factory=session_factory),
        sender=HttpWebhookSender(
            timeout_seconds=settings.dispatcher.webhook_timeout_seconds,
        ),
        retry_policy=ExponentialBackoffPolicy(
            base_seconds=settings.dispatcher.retry_base_seconds,
            max_seconds=settings.dispatcher.retry_max_seconds,
            jitter_seconds=settings.dispatcher.retry_jitter_seconds,
        ),
        max_attempts=settings.dispatcher.max_retries + 1,
    )
