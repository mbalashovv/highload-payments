from __future__ import annotations

from datetime import UTC, datetime, timedelta

from highload_payments.domain.value_objects.outbox_status import OutboxStatus
from highload_payments.infrastructure.db.repositories.outbox import SqlAlchemyOutboxRepository
from tests.factories import make_outbox_event


async def test_outbox_repository_add_and_claim_due_events(db_session) -> None:
    pending_event = make_outbox_event()
    due_retry_event = make_outbox_event()
    due_retry_event.status = OutboxStatus.RETRY
    due_retry_event.next_retry_at = datetime.now(tz=UTC) - timedelta(seconds=1)
    future_retry_event = make_outbox_event()
    future_retry_event.status = OutboxStatus.RETRY
    future_retry_event.next_retry_at = datetime.now(tz=UTC) + timedelta(minutes=5)
    repository = SqlAlchemyOutboxRepository(db_session)

    await repository.add(pending_event)
    await repository.add(due_retry_event)
    await repository.add(future_retry_event)
    await db_session.commit()

    claimed = await repository.claim_batch(size=10)

    claimed_ids = {event.event_id for event in claimed}
    assert pending_event.event_id in claimed_ids
    assert due_retry_event.event_id in claimed_ids
    assert future_retry_event.event_id not in claimed_ids


async def test_outbox_repository_update_persists_changed_fields(db_session) -> None:
    event = make_outbox_event()
    repository = SqlAlchemyOutboxRepository(db_session)

    await repository.add(event)
    await db_session.commit()

    event.schedule_retry(delay_seconds=5, reason="temporary error")
    await repository.update(event)
    await db_session.commit()

    claimed = await repository.claim_batch(size=10)
    stored = next(item for item in claimed if item.event_id == event.event_id)
    assert stored.status == OutboxStatus.RETRY
    assert stored.attempts == 1
    assert stored.last_error == "temporary error"

