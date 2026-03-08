from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from highload_payments.domain.value_objects.webhook_delivery_status import (
    WebhookDeliveryStatus,
)
from highload_payments.infrastructure.db.models.outbox_event import OutboxEventModel
from highload_payments.infrastructure.db.models.webhook_endpoint import WebhookEndpointModel
from highload_payments.infrastructure.db.repositories.webhook_delivery_state import (
    SqlAlchemyWebhookDeliveryStateRepository,
)
from tests.factories import make_outbox_event, make_webhook_endpoint


async def test_webhook_delivery_state_repository_initializes_once_per_event_endpoint(
    db_session,
) -> None:
    event = make_outbox_event()
    endpoint_one = make_webhook_endpoint()
    endpoint_two = make_webhook_endpoint()
    db_session.add(
        OutboxEventModel(
            event_id=event.event_id,
            aggregate_id=event.aggregate_id,
            event_type=event.event_type,
            payload=event.payload,
            status=event.status.value,
            attempts=event.attempts,
            next_retry_at=event.next_retry_at,
            last_error=event.last_error,
            created_at=event.created_at,
            processed_at=event.processed_at,
        )
    )
    db_session.add_all(
        [
            WebhookEndpointModel(
                endpoint_id=endpoint_one.endpoint_id,
                account_id=endpoint_one.account_id,
                url=endpoint_one.url,
                secret=endpoint_one.secret,
            ),
            WebhookEndpointModel(
                endpoint_id=endpoint_two.endpoint_id,
                account_id=endpoint_two.account_id,
                url=endpoint_two.url,
                secret=endpoint_two.secret,
            ),
        ]
    )
    await db_session.commit()
    repository = SqlAlchemyWebhookDeliveryStateRepository(db_session)

    await repository.initialize_for_event(
        event_id=event.event_id,
        endpoint_ids=[endpoint_one.endpoint_id, endpoint_two.endpoint_id],
    )
    await repository.initialize_for_event(
        event_id=event.event_id,
        endpoint_ids=[endpoint_one.endpoint_id, endpoint_two.endpoint_id],
    )
    await db_session.commit()

    states = await repository.get_by_event(event.event_id)

    assert len(states) == 2
    assert {state.status for state in states} == {WebhookDeliveryStatus.PENDING}


async def test_webhook_delivery_state_repository_returns_only_due_states(
    db_session,
) -> None:
    event = make_outbox_event()
    endpoint_one = make_webhook_endpoint()
    endpoint_two = make_webhook_endpoint()
    endpoint_three = make_webhook_endpoint()
    db_session.add(
        OutboxEventModel(
            event_id=event.event_id,
            aggregate_id=event.aggregate_id,
            event_type=event.event_type,
            payload=event.payload,
            status=event.status.value,
            attempts=event.attempts,
            next_retry_at=event.next_retry_at,
            last_error=event.last_error,
            created_at=event.created_at,
            processed_at=event.processed_at,
        )
    )
    db_session.add_all(
        [
            WebhookEndpointModel(
                endpoint_id=endpoint_one.endpoint_id,
                account_id=endpoint_one.account_id,
                url=endpoint_one.url,
                secret=endpoint_one.secret,
            ),
            WebhookEndpointModel(
                endpoint_id=endpoint_two.endpoint_id,
                account_id=endpoint_two.account_id,
                url=endpoint_two.url,
                secret=endpoint_two.secret,
            ),
            WebhookEndpointModel(
                endpoint_id=endpoint_three.endpoint_id,
                account_id=endpoint_three.account_id,
                url=endpoint_three.url,
                secret=endpoint_three.secret,
            ),
        ]
    )
    await db_session.commit()
    repository = SqlAlchemyWebhookDeliveryStateRepository(db_session)
    await repository.initialize_for_event(
        event_id=event.event_id,
        endpoint_ids=[
            endpoint_one.endpoint_id,
            endpoint_two.endpoint_id,
            endpoint_three.endpoint_id,
        ],
    )
    await db_session.commit()
    states = await repository.get_by_event(event.event_id)
    states_by_endpoint = {state.endpoint_id: state for state in states}
    pending_state = states_by_endpoint[endpoint_one.endpoint_id]
    retry_due_state = states_by_endpoint[endpoint_two.endpoint_id]
    retry_future_state = states_by_endpoint[endpoint_three.endpoint_id]
    retry_due_state.status = WebhookDeliveryStatus.RETRY
    retry_due_state.next_retry_at = datetime.now(tz=UTC) - timedelta(seconds=1)
    retry_future_state.status = WebhookDeliveryStatus.RETRY
    retry_future_state.next_retry_at = datetime.now(tz=UTC) + timedelta(minutes=5)
    await repository.update(retry_due_state)
    await repository.update(retry_future_state)
    await db_session.commit()

    due_states = await repository.get_due_by_event(event.event_id, size=10)

    due_ids = {state.endpoint_id for state in due_states}
    assert pending_state.endpoint_id in due_ids
    assert retry_due_state.endpoint_id in due_ids
    assert retry_future_state.endpoint_id not in due_ids
