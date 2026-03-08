from __future__ import annotations

from sqlalchemy import select

from highload_payments.infrastructure.db.models.outbox_event import OutboxEventModel
from highload_payments.infrastructure.db.models.payment import PaymentModel


async def test_create_payment_endpoint_persists_payment_and_outbox(
    integration_api_client,
    db_session_factory,
) -> None:
    account_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

    response = integration_api_client.post(
        "/payments",
        json={
            "account_id": account_id,
            "amount_minor": 1500,
            "currency": "USD",
            "idempotency_key": "integration-key-1",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "created"
    assert payload["duplicated"] is False

    async with db_session_factory() as session:
        payments = (await session.execute(select(PaymentModel))).scalars().all()
        outbox_events = (await session.execute(select(OutboxEventModel))).scalars().all()

    assert len(payments) == 1
    assert len(outbox_events) == 1
    assert str(payments[0].payment_id) == payload["payment_id"]
    assert outbox_events[0].aggregate_id == payments[0].payment_id
