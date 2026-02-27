from uuid import UUID

from highload_payments.application.ports.idempotency import IdempotencyStorePort


class InMemoryIdempotencyStore(IdempotencyStorePort):
    def __init__(self) -> None:
        self._storage: dict[str, UUID] = {}

    async def get_payment_id(self, client_key: str) -> UUID | None:
        return self._storage.get(client_key)

    async def save_payment_id(self, client_key: str, payment_id: UUID) -> None:
        self._storage[client_key] = payment_id

