from highload_payments.application.use_cases.deliver_webhook_event import (
    DeliverWebhookEventUseCase,
)
from highload_payments.infrastructure.db.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork
from highload_payments.infrastructure.delivery.webhook.http_sender import HttpWebhookSender
from highload_payments.infrastructure.settings import DispatcherSettings


def build_deliver_webhook_use_case(settings: DispatcherSettings) -> DeliverWebhookEventUseCase:
    return DeliverWebhookEventUseCase(
        uow=SqlAlchemyUnitOfWork(db_config=settings.db),
        sender=HttpWebhookSender(
            timeout_seconds=settings.dispatcher.webhook_timeout_seconds,
        ),
    )
