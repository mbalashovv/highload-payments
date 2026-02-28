from highload_payments.application.ports.delivery import DeliveryResult, WebhookSenderPort
from highload_payments.domain.entities.webhook_endpoint import WebhookEndpoint


class HttpWebhookSender(WebhookSenderPort):
    def __init__(self, timeout_seconds: float) -> None:
        self._timeout_seconds = timeout_seconds

    async def send(
        self,
        endpoint: WebhookEndpoint,
        event_type: str,
        payload: dict,
    ) -> DeliveryResult:
        raise NotImplementedError
