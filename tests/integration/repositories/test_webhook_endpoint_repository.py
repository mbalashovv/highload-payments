from __future__ import annotations

from highload_payments.infrastructure.db.models.webhook_endpoint import WebhookEndpointModel
from highload_payments.infrastructure.db.repositories.webhook_endpoint import (
    SqlAlchemyWebhookEndpointRepository,
)
from tests.factories import make_webhook_endpoint


async def test_webhook_endpoint_repository_returns_endpoints_for_account(
    db_session,
) -> None:
    target_endpoint = make_webhook_endpoint()
    another_endpoint = make_webhook_endpoint(account_id=target_endpoint.account_id)
    foreign_endpoint = make_webhook_endpoint()
    db_session.add_all(
        [
            WebhookEndpointModel(
                endpoint_id=target_endpoint.endpoint_id,
                account_id=target_endpoint.account_id,
                url=target_endpoint.url,
                secret=target_endpoint.secret,
            ),
            WebhookEndpointModel(
                endpoint_id=another_endpoint.endpoint_id,
                account_id=another_endpoint.account_id,
                url=another_endpoint.url,
                secret=another_endpoint.secret,
            ),
            WebhookEndpointModel(
                endpoint_id=foreign_endpoint.endpoint_id,
                account_id=foreign_endpoint.account_id,
                url=foreign_endpoint.url,
                secret=foreign_endpoint.secret,
            ),
        ]
    )
    await db_session.commit()
    repository = SqlAlchemyWebhookEndpointRepository(db_session)

    endpoints = await repository.get_by_account(target_endpoint.account_id)

    endpoint_ids = {endpoint.endpoint_id for endpoint in endpoints}
    assert endpoint_ids == {
        target_endpoint.endpoint_id,
        another_endpoint.endpoint_id,
    }

