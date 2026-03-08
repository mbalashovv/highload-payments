from __future__ import annotations

from tests.factories import make_outbox_event
from highload_payments.domain.value_objects.outbox_status import OutboxStatus


def test_create_sets_pending_defaults() -> None:
    event = make_outbox_event()

    assert event.status == OutboxStatus.PENDING
    assert event.attempts == 0
    assert event.next_retry_at is None
    assert event.last_error is None
    assert event.processed_at is None


def test_mark_published_sets_terminal_publish_fields() -> None:
    event = make_outbox_event()

    event.mark_published()

    assert event.status == OutboxStatus.PUBLISHED
    assert event.processed_at is not None
    assert event.last_error is None


def test_schedule_retry_increments_attempts_and_sets_delay() -> None:
    event = make_outbox_event()

    event.schedule_retry(delay_seconds=5, reason="broker unavailable")

    assert event.status == OutboxStatus.RETRY
    assert event.attempts == 1
    assert event.last_error == "broker unavailable"
    assert event.next_retry_at is not None


def test_mark_dead_increments_attempts_and_clears_retry() -> None:
    event = make_outbox_event()
    event.schedule_retry(delay_seconds=5, reason="temporary issue")

    event.mark_dead(reason="max attempts reached")

    assert event.status == OutboxStatus.DEAD
    assert event.attempts == 2
    assert event.last_error == "max attempts reached"
    assert event.next_retry_at is None
    assert event.processed_at is not None
