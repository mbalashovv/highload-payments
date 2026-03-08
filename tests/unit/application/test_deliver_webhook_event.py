from __future__ import annotations

from highload_payments.application.policies.retry import ExponentialBackoffPolicy
from highload_payments.application.ports.delivery import DeliveryResult
from highload_payments.application.use_cases.deliver_webhook_event import (
    DeliverWebhookEventUseCase,
)
from highload_payments.domain.value_objects.webhook_delivery_status import (
    WebhookDeliveryStatus,
)
from tests.factories import make_deliver_webhook_command, make_webhook_endpoint


async def test_deliver_webhook_event_initializes_states_and_sends_all_endpoints_once(
    fake_uow,
    recording_webhook_sender,
    seed_webhook_endpoints,
) -> None:
    command = make_deliver_webhook_command()
    endpoints = [
        make_webhook_endpoint(account_id=command.account_id),
        make_webhook_endpoint(account_id=command.account_id),
    ]
    seed_webhook_endpoints(endpoints)
    use_case = DeliverWebhookEventUseCase(
        uow=fake_uow,
        sender=recording_webhook_sender,
        retry_policy=ExponentialBackoffPolicy(base_seconds=1, max_seconds=10, jitter_seconds=0),
        max_attempts=3,
    )

    outcome = await use_case.execute(command)
    states = fake_uow.webhook_delivery_states.items

    assert outcome.delivered_count == 2
    assert outcome.should_retry is False
    assert len(recording_webhook_sender.calls) == 2
    assert len(states) == 2
    assert {state.status for state in states.values()} == {WebhookDeliveryStatus.SUCCEEDED}


async def test_deliver_webhook_event_retries_only_failed_endpoint(
    fake_uow,
    recording_webhook_sender,
    seed_webhook_endpoints,
) -> None:
    command = make_deliver_webhook_command()
    ok_endpoint = make_webhook_endpoint(account_id=command.account_id)
    flaky_endpoint = make_webhook_endpoint(account_id=command.account_id)
    seed_webhook_endpoints([ok_endpoint, flaky_endpoint])
    recording_webhook_sender.queue_response(
        flaky_endpoint.endpoint_id,
        DeliveryResult(
            delivered=False,
            retryable=True,
            status_code=503,
            detail="temporary failure",
        ),
    )
    use_case = DeliverWebhookEventUseCase(
        uow=fake_uow,
        sender=recording_webhook_sender,
        retry_policy=ExponentialBackoffPolicy(base_seconds=1, max_seconds=10, jitter_seconds=0),
        max_attempts=3,
    )

    first_outcome = await use_case.execute(command)
    first_call_ids = [call.endpoint_id for call in recording_webhook_sender.calls]
    flaky_state = fake_uow.webhook_delivery_states.items[
        (command.event_id, flaky_endpoint.endpoint_id)
    ]
    ok_state = fake_uow.webhook_delivery_states.items[
        (command.event_id, ok_endpoint.endpoint_id)
    ]

    assert first_outcome.delivered_count == 1
    assert first_outcome.retry_count == 1
    assert first_outcome.should_retry is True
    assert first_call_ids.count(ok_endpoint.endpoint_id) == 1
    assert first_call_ids.count(flaky_endpoint.endpoint_id) == 1
    assert ok_state.status == WebhookDeliveryStatus.SUCCEEDED
    assert flaky_state.status == WebhookDeliveryStatus.RETRY

    flaky_state.next_retry_at = None

    second_outcome = await use_case.execute(command)
    second_call_ids = [call.endpoint_id for call in recording_webhook_sender.calls]

    assert second_outcome.delivered_count == 1
    assert second_outcome.should_retry is False
    assert second_call_ids.count(ok_endpoint.endpoint_id) == 1
    assert second_call_ids.count(flaky_endpoint.endpoint_id) == 2
    assert flaky_state.status == WebhookDeliveryStatus.SUCCEEDED


async def test_deliver_webhook_event_marks_terminal_failure_after_max_attempts(
    fake_uow,
    recording_webhook_sender,
    seed_webhook_endpoints,
) -> None:
    command = make_deliver_webhook_command()
    endpoint = make_webhook_endpoint(account_id=command.account_id)
    seed_webhook_endpoints([endpoint])
    recording_webhook_sender.queue_response(
        endpoint.endpoint_id,
        DeliveryResult(
            delivered=False,
            retryable=False,
            status_code=400,
            detail="bad request",
        ),
    )
    use_case = DeliverWebhookEventUseCase(
        uow=fake_uow,
        sender=recording_webhook_sender,
        retry_policy=ExponentialBackoffPolicy(base_seconds=1, max_seconds=10, jitter_seconds=0),
        max_attempts=3,
    )

    outcome = await use_case.execute(command)
    state = fake_uow.webhook_delivery_states.items[(command.event_id, endpoint.endpoint_id)]

    assert outcome.delivered_count == 0
    assert outcome.terminal_failures == 1
    assert outcome.should_retry is False
    assert state.status == WebhookDeliveryStatus.FAILED_TERMINAL
    assert state.last_status_code == 400
    assert state.last_error == "bad request"
