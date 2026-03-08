from __future__ import annotations

from highload_payments.application.policies.retry import ExponentialBackoffPolicy
from highload_payments.application.use_cases.publish_outbox_batch import (
    PublishOutboxBatchUseCase,
)
from highload_payments.domain.value_objects.outbox_status import OutboxStatus
from tests.factories import make_outbox_event


async def test_publish_outbox_batch_marks_event_published(
    fake_uow,
    recording_publisher,
) -> None:
    event = make_outbox_event()
    fake_uow.outbox.items[event.event_id] = event
    use_case = PublishOutboxBatchUseCase(
        uow=fake_uow,
        publisher=recording_publisher,
        retry_policy=ExponentialBackoffPolicy(base_seconds=1, max_seconds=10, jitter_seconds=0),
        max_attempts=3,
    )

    processed = await use_case.execute(batch_size=10)

    assert processed == 1
    assert event.status == OutboxStatus.PUBLISHED
    assert event.processed_at is not None
    assert recording_publisher.published_events == [event]
    assert fake_uow.commit_calls == 1


async def test_publish_outbox_batch_schedules_retry_on_publish_failure(
    fake_uow,
    recording_publisher,
) -> None:
    event = make_outbox_event()
    fake_uow.outbox.items[event.event_id] = event
    recording_publisher.failures_remaining = 1
    use_case = PublishOutboxBatchUseCase(
        uow=fake_uow,
        publisher=recording_publisher,
        retry_policy=ExponentialBackoffPolicy(base_seconds=5, max_seconds=10, jitter_seconds=0),
        max_attempts=3,
    )

    processed = await use_case.execute(batch_size=10)

    assert processed == 1
    assert event.status == OutboxStatus.RETRY
    assert event.attempts == 1
    assert event.next_retry_at is not None
    assert event.last_error == "publisher failure"


async def test_publish_outbox_batch_marks_dead_when_attempt_limit_reached(
    fake_uow,
    recording_publisher,
) -> None:
    event = make_outbox_event()
    event.attempts = 2
    fake_uow.outbox.items[event.event_id] = event
    recording_publisher.failures_remaining = 1
    use_case = PublishOutboxBatchUseCase(
        uow=fake_uow,
        publisher=recording_publisher,
        retry_policy=ExponentialBackoffPolicy(base_seconds=1, max_seconds=10, jitter_seconds=0),
        max_attempts=3,
    )

    processed = await use_case.execute(batch_size=10)

    assert processed == 1
    assert event.status == OutboxStatus.DEAD
    assert event.attempts == 3
    assert event.processed_at is not None
    assert event.last_error == "publisher failure"

