from highload_payments.application.policies.retry import ExponentialBackoffPolicy
from highload_payments.application.use_cases.publish_outbox_batch import (
    PublishOutboxBatchUseCase,
)
from highload_payments.infrastructure.db.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork
from highload_payments.infrastructure.messaging.jetstream.publisher import JetStreamPublisher


def build_publish_outbox_use_case() -> PublishOutboxBatchUseCase:
    return PublishOutboxBatchUseCase(
        uow=SqlAlchemyUnitOfWork(),
        publisher=JetStreamPublisher(),
        retry_policy=ExponentialBackoffPolicy(),
    )

