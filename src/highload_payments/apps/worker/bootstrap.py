from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from highload_payments.application.policies.retry import ExponentialBackoffPolicy
from highload_payments.application.use_cases.publish_outbox_batch import (
    PublishOutboxBatchUseCase,
)
from highload_payments.infrastructure.db.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork
from highload_payments.infrastructure.messaging.jetstream.publisher import JetStreamPublisher
from highload_payments.infrastructure.settings import WorkerSettings


def build_publish_outbox_use_case(
    settings: WorkerSettings,
    session_factory: async_sessionmaker[AsyncSession],
) -> PublishOutboxBatchUseCase:
    return PublishOutboxBatchUseCase(
        uow=SqlAlchemyUnitOfWork(session_factory=session_factory),
        publisher=JetStreamPublisher(nats_config=settings.nats),
        retry_policy=ExponentialBackoffPolicy(
            base_seconds=settings.worker.retry_base_seconds,
            max_seconds=settings.worker.retry_max_seconds,
            jitter_seconds=settings.worker.retry_jitter_seconds,
        ),
        max_attempts=settings.worker.max_attempts,
    )
