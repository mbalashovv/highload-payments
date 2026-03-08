from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

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
from highload_payments.infrastructure.idempotency.in_memory_store import (
    InMemoryIdempotencyStore,
)


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
