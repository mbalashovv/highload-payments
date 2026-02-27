from dataclasses import dataclass
from typing import Protocol

from highload_payments.domain.entities.webhook_endpoint import WebhookEndpoint


@dataclass(frozen=True, slots=True)
class DeliveryResult:
    delivered: bool
    retryable: bool
    status_code: int | None
    detail: str


class WebhookSenderPort(Protocol):
    async def send(
        self,
        endpoint: WebhookEndpoint,
        event_type: str,
        payload: dict,
    ) -> DeliveryResult: ...

