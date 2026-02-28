from highload_payments.application.policies.retry import ExponentialBackoffPolicy
from highload_payments.application.use_cases.publish_outbox_batch import (
    PublishOutboxBatchUseCase,
)
from highload_payments.infrastructure.db.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork
from highload_payments.infrastructure.messaging.jetstream.publisher import JetStreamPublisher
from highload_payments.infrastructure.settings import WorkerSettings


def build_publish_outbox_use_case(settings: WorkerSettings) -> PublishOutboxBatchUseCase:
    return PublishOutboxBatchUseCase(
        uow=SqlAlchemyUnitOfWork(db_config=settings.db),
        publisher=JetStreamPublisher(nats_config=settings.nats),
        retry_policy=ExponentialBackoffPolicy(),
    )
