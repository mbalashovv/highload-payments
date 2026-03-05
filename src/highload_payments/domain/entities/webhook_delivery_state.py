from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from highload_payments.domain.value_objects.webhook_delivery_status import (
    WebhookDeliveryStatus,
)


@dataclass(slots=True)
class WebhookDeliveryState:
    event_id: UUID
    endpoint_id: UUID
    status: WebhookDeliveryStatus
    attempts: int
    next_retry_at: datetime | None
    last_error: str | None
    last_status_code: int | None
    created_at: datetime
    updated_at: datetime
    delivered_at: datetime | None

    @classmethod
    def create_pending(
        cls,
        event_id: UUID,
        endpoint_id: UUID,
        now: datetime | None = None,
    ) -> "WebhookDeliveryState":
        ts = now or datetime.now(tz=UTC)
        return cls(
            event_id=event_id,
            endpoint_id=endpoint_id,
            status=WebhookDeliveryStatus.PENDING,
            attempts=0,
            next_retry_at=None,
            last_error=None,
            last_status_code=None,
            created_at=ts,
            updated_at=ts,
            delivered_at=None,
        )

    def mark_succeeded(self, status_code: int | None = None) -> None:
        self.attempts += 1
        self.status = WebhookDeliveryStatus.SUCCEEDED
        self.last_status_code = status_code
        self.last_error = None
        self.next_retry_at = None
        ts = datetime.now(tz=UTC)
        self.updated_at = ts
        self.delivered_at = ts

    def schedule_retry(
        self,
        delay_seconds: int,
        reason: str,
        status_code: int | None = None,
    ) -> None:
        self.attempts += 1
        self.status = WebhookDeliveryStatus.RETRY
        self.last_error = reason
        self.last_status_code = status_code
        self.next_retry_at = datetime.now(tz=UTC) + timedelta(seconds=delay_seconds)
        self.updated_at = datetime.now(tz=UTC)

    def mark_terminal_failure(
        self,
        reason: str,
        status_code: int | None = None,
    ) -> None:
        self.attempts += 1
        self.status = WebhookDeliveryStatus.FAILED_TERMINAL
        self.last_error = reason
        self.last_status_code = status_code
        self.next_retry_at = None
        self.updated_at = datetime.now(tz=UTC)
