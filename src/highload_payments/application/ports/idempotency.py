from typing import Protocol
from uuid import UUID


class IdempotencyStorePort(Protocol):
    async def get_payment_id(self, client_key: str) -> UUID | None: ...

    async def save_payment_id(self, client_key: str, payment_id: UUID) -> None: ...

