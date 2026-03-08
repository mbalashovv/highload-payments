from __future__ import annotations

from uuid import UUID, uuid4

from highload_payments.domain.entities.outbox_event import OutboxEvent


def make_outbox_event(
    *,
    event_id: UUID | None = None,
    aggregate_id: UUID | None = None,
    event_type: str = "payment.created",
    payload: dict | None = None,
) -> OutboxEvent:
    return OutboxEvent.create(
        event_id=event_id or uuid4(),
        aggregate_id=aggregate_id or uuid4(),
        event_type=event_type,
        payload=payload or {},
    )
