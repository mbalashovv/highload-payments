from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select
from sqlalchemy.dialects.postgresql import insert

from highload_payments.application.ports.repositories import (
    WebhookDeliveryStateRepository,
)
from highload_payments.domain.entities.webhook_delivery_state import (
    WebhookDeliveryState,
)
from highload_payments.domain.value_objects.webhook_delivery_status import (
    WebhookDeliveryStatus,
)
from highload_payments.infrastructure.db.models.webhook_delivery_state import (
    WebhookDeliveryStateModel,
)
from highload_payments.infrastructure.db.repositories.base import SqlAlchemyRepository


class SqlAlchemyWebhookDeliveryStateRepository(
    SqlAlchemyRepository,
    WebhookDeliveryStateRepository,
):
    async def initialize_for_event(
        self,
        event_id: UUID,
        endpoint_ids: list[UUID],
    ) -> None:
        if not endpoint_ids:
            return

        now = datetime.now(tz=UTC)
        values = [
            {
                "id": uuid4(),
                "event_id": event_id,
                "endpoint_id": endpoint_id,
                "status": WebhookDeliveryStatus.PENDING.value,
                "attempts": 0,
                "next_retry_at": None,
                "last_error": None,
                "last_status_code": None,
                "created_at": now,
                "updated_at": now,
                "delivered_at": None,
            }
            for endpoint_id in endpoint_ids
        ]

        statement = insert(WebhookDeliveryStateModel).values(values)
        statement = statement.on_conflict_do_nothing(
            index_elements=["event_id", "endpoint_id"],
        )
        await self._session.execute(statement)

    async def get_due_by_event(
        self,
        event_id: UUID,
        size: int,
    ) -> list[WebhookDeliveryState]:
        now = datetime.now(tz=UTC)
        statement = (
            select(WebhookDeliveryStateModel)
            .where(
                WebhookDeliveryStateModel.event_id == event_id,
                or_(
                    WebhookDeliveryStateModel.status
                    == WebhookDeliveryStatus.PENDING.value,
                    and_(
                        WebhookDeliveryStateModel.status
                        == WebhookDeliveryStatus.RETRY.value,
                        or_(
                            WebhookDeliveryStateModel.next_retry_at.is_(None),
                            WebhookDeliveryStateModel.next_retry_at <= now,
                        ),
                    ),
                ),
            )
            .order_by(WebhookDeliveryStateModel.created_at.asc())
            .limit(size)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(statement)
        rows = result.scalars().all()
        return [self._to_domain(row) for row in rows]

    async def get_by_event(self, event_id: UUID) -> list[WebhookDeliveryState]:
        statement = select(WebhookDeliveryStateModel).where(
            WebhookDeliveryStateModel.event_id == event_id
        )
        result = await self._session.execute(statement)
        rows = result.scalars().all()
        return [self._to_domain(row) for row in rows]

    async def update(self, state: WebhookDeliveryState) -> None:
        statement = select(WebhookDeliveryStateModel).where(
            WebhookDeliveryStateModel.event_id == state.event_id,
            WebhookDeliveryStateModel.endpoint_id == state.endpoint_id,
        )
        result = await self._session.execute(statement)
        row = result.scalars().first()
        if row is None:
            raise ValueError(
                "Webhook delivery state does not exist for "
                f"event_id={state.event_id} endpoint_id={state.endpoint_id}"
            )
        row.status = state.status.value
        row.attempts = state.attempts
        row.next_retry_at = state.next_retry_at
        row.last_error = state.last_error
        row.last_status_code = state.last_status_code
        row.updated_at = state.updated_at
        row.delivered_at = state.delivered_at

    @staticmethod
    def _to_domain(row: WebhookDeliveryStateModel) -> WebhookDeliveryState:
        return WebhookDeliveryState(
            event_id=row.event_id,
            endpoint_id=row.endpoint_id,
            status=WebhookDeliveryStatus(row.status),
            attempts=row.attempts,
            next_retry_at=row.next_retry_at,
            last_error=row.last_error,
            last_status_code=row.last_status_code,
            created_at=row.created_at,
            updated_at=row.updated_at,
            delivered_at=row.delivered_at,
        )
