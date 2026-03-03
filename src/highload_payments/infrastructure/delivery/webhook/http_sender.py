import httpx

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
        body = {"event_type": event_type, "payload": payload}
        headers = {"Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.post(endpoint.url, json=body, headers=headers)
        except httpx.TimeoutException as exc:
            return DeliveryResult(
                delivered=False,
                retryable=True,
                status_code=None,
                detail=f"timeout: {exc}",
            )
        except httpx.HTTPError as exc:
            return DeliveryResult(
                delivered=False,
                retryable=True,
                status_code=None,
                detail=f"http error: {exc}",
            )

        delivered = 200 <= response.status_code < 300
        retryable = response.status_code >= 500
        return DeliveryResult(
            delivered=delivered,
            retryable=retryable,
            status_code=response.status_code,
            detail=response.text[:512],
        )
