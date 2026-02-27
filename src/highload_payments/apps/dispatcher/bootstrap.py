from highload_payments.application.use_cases.deliver_webhook_event import (
    DeliverWebhookEventUseCase,
)
from highload_payments.infrastructure.db.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork
from highload_payments.infrastructure.delivery.webhook.http_sender import HttpWebhookSender


def build_deliver_webhook_use_case() -> DeliverWebhookEventUseCase:
    return DeliverWebhookEventUseCase(
        uow=SqlAlchemyUnitOfWork(),
        sender=HttpWebhookSender(),
    )

