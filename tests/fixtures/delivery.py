from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from uuid import UUID

import pytest

from highload_payments.application.ports.delivery import DeliveryResult
from highload_payments.domain.entities.webhook_endpoint import WebhookEndpoint


@dataclass(frozen=True, slots=True)
class DeliveryCall:
    endpoint_id: UUID
    event_type: str
    payload: dict


@dataclass(slots=True)
class RecordingWebhookSender:
    responses: dict[UUID, deque[DeliveryResult]] = field(
        default_factory=lambda: defaultdict(deque)
    )
    calls: list[DeliveryCall] = field(default_factory=list)

    async def send(
        self,
        endpoint: WebhookEndpoint,
        event_type: str,
        payload: dict,
    ) -> DeliveryResult:
        self.calls.append(
            DeliveryCall(
                endpoint_id=endpoint.endpoint_id,
                event_type=event_type,
                payload=payload,
            )
        )
        queue = self.responses[endpoint.endpoint_id]
        if queue:
            return queue.popleft()
        return DeliveryResult(
            delivered=True,
            retryable=False,
            status_code=200,
            detail="ok",
        )

    def queue_response(self, endpoint_id: UUID, result: DeliveryResult) -> None:
        self.responses[endpoint_id].append(result)


@pytest.fixture
def recording_webhook_sender() -> RecordingWebhookSender:
    return RecordingWebhookSender()
