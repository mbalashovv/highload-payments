from uuid import UUID

from sqlalchemy import select

from highload_payments.application.ports.repositories import WebhookEndpointRepository
from highload_payments.domain.entities.webhook_endpoint import WebhookEndpoint
from highload_payments.infrastructure.db.models.webhook_endpoint import WebhookEndpointModel
from highload_payments.infrastructure.db.repositories.base import SqlAlchemyRepository


class SqlAlchemyWebhookEndpointRepository(
    SqlAlchemyRepository,
    WebhookEndpointRepository,
):
    async def get_by_account(self, account_id: UUID) -> list[WebhookEndpoint]:
        statement = select(WebhookEndpointModel).where(
            WebhookEndpointModel.account_id == account_id
        )
        result = await self._session.execute(statement)
        rows = result.scalars().all()
        return [
            WebhookEndpoint(
                endpoint_id=row.endpoint_id,
                account_id=row.account_id,
                url=row.url,
                secret=row.secret,
            )
            for row in rows
        ]
