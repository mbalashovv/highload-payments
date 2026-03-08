from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
import os
from pathlib import Path
from uuid import UUID, uuid4

import asyncpg
import pytest
import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from highload_payments.application.ports.uow import UnitOfWork
from highload_payments.domain.entities.outbox_event import OutboxEvent
from highload_payments.domain.entities.payment import Payment
from highload_payments.domain.entities.webhook_delivery_state import (
    WebhookDeliveryState,
)
from highload_payments.domain.entities.webhook_endpoint import WebhookEndpoint
from highload_payments.domain.value_objects.outbox_status import OutboxStatus
from highload_payments.domain.value_objects.webhook_delivery_status import (
    WebhookDeliveryStatus,
)
from highload_payments.infrastructure.db.models import BaseModel
from highload_payments.infrastructure.db.models.outbox_event import OutboxEventModel
from highload_payments.infrastructure.db.models.payment import PaymentModel
from highload_payments.infrastructure.db.models.webhook_delivery_state import (
    WebhookDeliveryStateModel,
)
from highload_payments.infrastructure.db.models.webhook_endpoint import (
    WebhookEndpointModel,
)
from highload_payments.infrastructure.db.session import DbRuntime, create_db_runtime
from highload_payments.infrastructure.db.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork
from highload_payments.infrastructure.idempotency.in_memory_store import (
    InMemoryIdempotencyStore,
)
from highload_payments.infrastructure.settings import DbConfig


@dataclass(slots=True)
class InMemoryPaymentRepository:
    items: dict[UUID, Payment] = field(default_factory=dict)

    async def add(self, payment: Payment) -> None:
        self.items[payment.payment_id] = payment

    async def get(self, payment_id: UUID) -> Payment | None:
        return self.items.get(payment_id)


@dataclass(slots=True)
class InMemoryOutboxRepository:
    items: dict[UUID, OutboxEvent] = field(default_factory=dict)

    async def add(self, event: OutboxEvent) -> None:
        self.items[event.event_id] = event

    async def claim_batch(self, size: int) -> list[OutboxEvent]:
        now = datetime.now(tz=UTC)
        eligible = [
            event
            for event in self.items.values()
            if event.status == OutboxStatus.PENDING
            or (
                event.status == OutboxStatus.RETRY
                and (event.next_retry_at is None or event.next_retry_at <= now)
            )
        ]
        eligible.sort(key=lambda item: item.created_at)
        return eligible[:size]

    async def update(self, event: OutboxEvent) -> None:
        self.items[event.event_id] = event


@dataclass(slots=True)
class InMemoryWebhookEndpointRepository:
    items: dict[UUID, WebhookEndpoint] = field(default_factory=dict)

    async def get_by_account(self, account_id: UUID) -> list[WebhookEndpoint]:
        return [
            endpoint
            for endpoint in self.items.values()
            if endpoint.account_id == account_id
        ]


@dataclass(slots=True)
class InMemoryWebhookDeliveryStateRepository:
    items: dict[tuple[UUID, UUID], WebhookDeliveryState] = field(default_factory=dict)

    async def initialize_for_event(
        self,
        event_id: UUID,
        endpoint_ids: list[UUID],
    ) -> None:
        for endpoint_id in endpoint_ids:
            key = (event_id, endpoint_id)
            self.items.setdefault(
                key,
                WebhookDeliveryState.create_pending(
                    event_id=event_id,
                    endpoint_id=endpoint_id,
                ),
            )

    async def get_due_by_event(
        self,
        event_id: UUID,
        size: int,
    ) -> list[WebhookDeliveryState]:
        now = datetime.now(tz=UTC)
        due = [
            state
            for state in self.items.values()
            if state.event_id == event_id
            and (
                state.status == WebhookDeliveryStatus.PENDING
                or (
                    state.status == WebhookDeliveryStatus.RETRY
                    and (
                        state.next_retry_at is None or state.next_retry_at <= now
                    )
                )
            )
        ]
        due.sort(key=lambda item: item.created_at)
        return due[:size]

    async def get_by_event(self, event_id: UUID) -> list[WebhookDeliveryState]:
        return [state for state in self.items.values() if state.event_id == event_id]

    async def update(self, state: WebhookDeliveryState) -> None:
        self.items[(state.event_id, state.endpoint_id)] = state


@dataclass(slots=True)
class FakeUnitOfWork(UnitOfWork):
    payments: InMemoryPaymentRepository = field(default_factory=InMemoryPaymentRepository)
    outbox: InMemoryOutboxRepository = field(default_factory=InMemoryOutboxRepository)
    webhook_endpoints: InMemoryWebhookEndpointRepository = field(
        default_factory=InMemoryWebhookEndpointRepository
    )
    webhook_delivery_states: InMemoryWebhookDeliveryStateRepository = field(
        default_factory=InMemoryWebhookDeliveryStateRepository
    )
    commit_calls: int = 0
    rollback_calls: int = 0
    entered: bool = False

    async def __aenter__(self) -> "FakeUnitOfWork":
        self.entered = True
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self.entered = False
        if exc is not None:
            await self.rollback()

    async def commit(self) -> None:
        self.commit_calls += 1

    async def rollback(self) -> None:
        self.rollback_calls += 1


@dataclass(slots=True)
class SequentialIdGenerator:
    values: deque[UUID]

    def new(self) -> UUID:
        if not self.values:
            raise RuntimeError("SequentialIdGenerator is exhausted")
        return self.values.popleft()


@pytest.fixture
def fake_uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def in_memory_idempotency_store() -> InMemoryIdempotencyStore:
    return InMemoryIdempotencyStore()


@pytest.fixture
def sequential_id_generator() -> SequentialIdGenerator:
    return SequentialIdGenerator(values=deque([uuid4() for _ in range(16)]))


@pytest.fixture
def seed_webhook_endpoints(
    fake_uow: FakeUnitOfWork,
):
    def _seed(endpoints: Iterable[WebhookEndpoint]) -> None:
        for endpoint in endpoints:
            fake_uow.webhook_endpoints.items[endpoint.endpoint_id] = endpoint

    return _seed


@pytest.fixture(scope="session")
def test_db_config() -> DbConfig:
    return _load_test_db_config()


@pytest_asyncio.fixture(scope="session")
async def db_runtime(test_db_config: DbConfig) -> DbRuntime:
    if not await _ensure_test_database(test_db_config):
        pytest.skip("PostgreSQL is not available for integration tests")

    runtime = create_db_runtime(test_db_config)
    async with runtime.engine.begin() as connection:
        await connection.run_sync(BaseModel.metadata.create_all)
    yield runtime
    await runtime.dispose()


@pytest_asyncio.fixture
async def db_session_factory(
    db_runtime: DbRuntime,
) -> async_sessionmaker[AsyncSession]:
    await _truncate_tables(db_runtime)
    return db_runtime.session_factory


@pytest_asyncio.fixture
async def db_session(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncSession:
    async with db_session_factory() as session:
        yield session


@pytest.fixture
def sql_uow(
    db_session_factory: async_sessionmaker[AsyncSession],
) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(session_factory=db_session_factory)


def _load_test_db_config() -> DbConfig:
    env = _read_env_file(Path(__file__).resolve().parents[2] / ".env")
    user = os.getenv("TEST_POSTGRES_USER", env.get("POSTGRES_USER", "admin"))
    password = os.getenv("TEST_POSTGRES_PASSWORD", env.get("POSTGRES_PASSWORD", "admin"))
    host = os.getenv("TEST_POSTGRES_HOST", "127.0.0.1")
    port = int(os.getenv("TEST_POSTGRES_PORT", env.get("POSTGRES_PORT", "5432")))
    database = os.getenv("TEST_POSTGRES_DB", "payments_test")
    return DbConfig(
        dsn=f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}",
        pool_size=5,
        max_overflow=5,
    )


async def _ensure_test_database(db_config: DbConfig) -> bool:
    database_name = db_config.dsn.rsplit("/", 1)[-1]
    admin_dsn = db_config.dsn.rsplit("/", 1)[0] + "/postgres"
    try:
        connection = await asyncpg.connect(admin_dsn.replace("+asyncpg", ""))
    except Exception:
        return False

    try:
        exists = await connection.fetchval(
            "select 1 from pg_database where datname = $1",
            database_name,
        )
        if not exists:
            await connection.execute(f'create database "{database_name}"')
    finally:
        await connection.close()
    return True


async def _truncate_tables(db_runtime: DbRuntime) -> None:
    async with db_runtime.engine.begin() as connection:
        for model in (
            WebhookDeliveryStateModel,
            WebhookEndpointModel,
            OutboxEventModel,
            PaymentModel,
        ):
            await connection.execute(delete(model))


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values
