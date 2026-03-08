from __future__ import annotations

from uuid import UUID, uuid4

from highload_payments.application.dto.commands import DeliverWebhookCommand
from highload_payments.domain.entities.webhook_delivery_state import (
    WebhookDeliveryState,
)
from highload_payments.domain.entities.webhook_endpoint import WebhookEndpoint


def make_webhook_endpoint(
    *,
    endpoint_id: UUID | None = None,
    account_id: UUID | None = None,
    url: str = "https://example.test/webhooks/payments",
    secret: str = "test-secret",
) -> WebhookEndpoint:
    return WebhookEndpoint(
        endpoint_id=endpoint_id or uuid4(),
        account_id=account_id or uuid4(),
        url=url,
        secret=secret,
    )


def make_webhook_delivery_state(
    *,
    event_id: UUID | None = None,
    endpoint_id: UUID | None = None,
) -> WebhookDeliveryState:
    return WebhookDeliveryState.create_pending(
        event_id=event_id or uuid4(),
        endpoint_id=endpoint_id or uuid4(),
    )


def make_deliver_webhook_command(
    *,
    event_id: UUID | None = None,
    payment_id: UUID | None = None,
    account_id: UUID | None = None,
    event_type: str = "payment.created",
    payload: dict | None = None,
) -> DeliverWebhookCommand:
    payment_uuid = payment_id or uuid4()
    account_uuid = account_id or uuid4()
    return DeliverWebhookCommand(
        event_id=event_id or uuid4(),
        payment_id=payment_uuid,
        account_id=account_uuid,
        event_type=event_type,
        payload=payload
        or {
            "payment_id": str(payment_uuid),
            "account_id": str(account_uuid),
            "amount_minor": 1500,
            "currency": "USD",
        },
    )
