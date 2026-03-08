from __future__ import annotations

from tests.factories import make_webhook_delivery_state
from highload_payments.domain.value_objects.webhook_delivery_status import (
    WebhookDeliveryStatus,
)


def test_create_pending_sets_initial_state() -> None:
    state = make_webhook_delivery_state()

    assert state.status == WebhookDeliveryStatus.PENDING
    assert state.attempts == 0
    assert state.next_retry_at is None
    assert state.last_error is None
    assert state.last_status_code is None
    assert state.delivered_at is None
    assert state.created_at == state.updated_at


def test_mark_succeeded_sets_delivery_fields() -> None:
    state = make_webhook_delivery_state()

    state.mark_succeeded(status_code=200)

    assert state.status == WebhookDeliveryStatus.SUCCEEDED
    assert state.attempts == 1
    assert state.last_status_code == 200
    assert state.last_error is None
    assert state.next_retry_at is None
    assert state.delivered_at is not None
    assert state.updated_at == state.delivered_at


def test_schedule_retry_sets_retry_state_and_delay() -> None:
    state = make_webhook_delivery_state()

    state.schedule_retry(
        delay_seconds=10,
        reason="timeout",
        status_code=503,
    )

    assert state.status == WebhookDeliveryStatus.RETRY
    assert state.attempts == 1
    assert state.last_error == "timeout"
    assert state.last_status_code == 503
    assert state.next_retry_at is not None
    assert state.delivered_at is None


def test_mark_terminal_failure_sets_terminal_fields() -> None:
    state = make_webhook_delivery_state()
    state.schedule_retry(delay_seconds=5, reason="temporary", status_code=500)

    state.mark_terminal_failure(reason="max attempts reached", status_code=500)

    assert state.status == WebhookDeliveryStatus.FAILED_TERMINAL
    assert state.attempts == 2
    assert state.last_error == "max attempts reached"
    assert state.last_status_code == 500
    assert state.next_retry_at is None
    assert state.delivered_at is None
