from highload_payments.application.ports.repositories import OutboxRepository
from highload_payments.domain.entities.outbox_event import OutboxEvent
from highload_payments.infrastructure.db.repositories.base import SqlAlchemyRepository


class SqlAlchemyOutboxRepository(SqlAlchemyRepository, OutboxRepository):
    async def add(self, event: OutboxEvent) -> None:
        raise NotImplementedError

    async def claim_batch(self, size: int) -> list[OutboxEvent]:
        raise NotImplementedError

    async def update(self, event: OutboxEvent) -> None:
        raise NotImplementedError
