from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from highload_payments.domain.value_objects.outbox_status import OutboxStatus


@dataclass(slots=True)
class OutboxEvent:
    event_id: UUID
    aggregate_id: UUID
    event_type: str
    payload: dict[str, Any]
    status: OutboxStatus
    attempts: int
    next_retry_at: datetime | None
    last_error: str | None
    created_at: datetime
    processed_at: datetime | None

    @classmethod
    def create(
        cls,
        event_id: UUID,
        aggregate_id: UUID,
        event_type: str,
        payload: dict[str, Any],
    ) -> "OutboxEvent":
        return cls(
            event_id=event_id,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=payload,
            status=OutboxStatus.PENDING,
            attempts=0,
            next_retry_at=None,
            last_error=None,
            created_at=datetime.now(tz=UTC),
            processed_at=None,
        )

    def mark_published(self) -> None:
        self.status = OutboxStatus.PUBLISHED
        self.processed_at = datetime.now(tz=UTC)
        self.last_error = None

    def schedule_retry(self, delay_seconds: int, reason: str) -> None:
        self.status = OutboxStatus.RETRY
        self.attempts += 1
        self.last_error = reason
        self.next_retry_at = datetime.now(tz=UTC) + timedelta(seconds=delay_seconds)

    def mark_dead(self, reason: str) -> None:
        self.status = OutboxStatus.DEAD
        self.attempts += 1
        self.last_error = reason
        self.next_retry_at = None
        self.processed_at = datetime.now(tz=UTC)
