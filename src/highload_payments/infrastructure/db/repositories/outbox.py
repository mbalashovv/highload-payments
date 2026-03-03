from datetime import UTC, datetime
import orjson
from typing import Any

from sqlalchemy import and_, or_, select

from highload_payments.application.ports.repositories import OutboxRepository
from highload_payments.domain.entities.outbox_event import OutboxEvent
from highload_payments.domain.value_objects.outbox_status import OutboxStatus
from highload_payments.infrastructure.db.models.outbox_event import OutboxEventModel
from highload_payments.infrastructure.db.repositories.base import SqlAlchemyRepository


class SqlAlchemyOutboxRepository(SqlAlchemyRepository, OutboxRepository):
    async def add(self, event: OutboxEvent) -> None:
        self._session.add(
            OutboxEventModel(
                event_id=event.event_id,
                aggregate_id=event.aggregate_id,
                event_type=event.event_type,
                payload=_normalize_payload(event.payload),
                status=event.status.value,
                attempts=event.attempts,
                next_retry_at=event.next_retry_at,
                last_error=event.last_error,
                created_at=event.created_at,
                processed_at=event.processed_at,
            )
        )

    async def claim_batch(self, size: int) -> list[OutboxEvent]:
        now = datetime.now(tz=UTC)
        statement = (
            select(OutboxEventModel)
            .where(
                or_(
                    OutboxEventModel.status == OutboxStatus.PENDING.value,
                    and_(
                        OutboxEventModel.status == OutboxStatus.RETRY.value,
                        or_(
                            OutboxEventModel.next_retry_at.is_(None),
                            OutboxEventModel.next_retry_at <= now,
                        ),
                    ),
                )
            )
            .order_by(OutboxEventModel.created_at.asc())
            .limit(size)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(statement)
        rows = result.scalars().all()
        return [self._to_domain(row) for row in rows]

    async def update(self, event: OutboxEvent) -> None:
        row = await self._session.get(OutboxEventModel, event.event_id)
        if row is None:
            raise ValueError(f"Outbox event {event.event_id} does not exist")
        row.status = event.status.value
        row.attempts = event.attempts
        row.next_retry_at = event.next_retry_at
        row.last_error = event.last_error
        row.processed_at = event.processed_at
        row.payload = _normalize_payload(event.payload)

    @staticmethod
    def _to_domain(row: OutboxEventModel) -> OutboxEvent:
        payload: dict[str, Any]
        if isinstance(row.payload, dict):
            payload = row.payload
        else:
            payload = {}

        return OutboxEvent(
            event_id=row.event_id,
            aggregate_id=row.aggregate_id,
            event_type=row.event_type,
            payload=payload,
            status=OutboxStatus(row.status),
            attempts=row.attempts,
            next_retry_at=row.next_retry_at,
            last_error=row.last_error,
            created_at=row.created_at,
            processed_at=row.processed_at,
        )


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return orjson.loads(orjson.dumps(payload, default=str))
