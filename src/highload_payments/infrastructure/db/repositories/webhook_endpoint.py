from uuid import UUID

from highload_payments.application.ports.repositories import WebhookEndpointRepository
from highload_payments.domain.entities.webhook_endpoint import WebhookEndpoint
from highload_payments.infrastructure.db.repositories.base import SqlAlchemyRepository


class SqlAlchemyWebhookEndpointRepository(
    SqlAlchemyRepository,
    WebhookEndpointRepository,
):
    async def get_by_account(self, account_id: UUID) -> list[WebhookEndpoint]:
        raise NotImplementedError
