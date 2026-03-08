from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from highload_payments.application.dto.commands import CreatePaymentCommand
from highload_payments.application.dto.results import PaymentResult
from highload_payments.apps.api.bootstrap import build_create_payment_use_case
from highload_payments.apps.api.http.routes import setup_controllers
from highload_payments.domain.value_objects.payment_status import PaymentStatus
from highload_payments.infrastructure.settings import (
    ApiConfig,
    ApiSettings,
    CommonConfig,
    DbConfig,
    NatsConfig,
)


@dataclass(slots=True)
class StubCreatePaymentUseCase:
    result: PaymentResult = field(
        default_factory=lambda: PaymentResult(
            payment_id=uuid4(),
            status=PaymentStatus.CREATED,
            duplicated=False,
        )
    )
    commands: list[CreatePaymentCommand] = field(default_factory=list)

    async def execute(self, command: CreatePaymentCommand) -> PaymentResult:
        self.commands.append(command)
        return self.result


@pytest.fixture
def stub_create_payment_use_case() -> StubCreatePaymentUseCase:
    return StubCreatePaymentUseCase()


@pytest.fixture
def api_app(stub_create_payment_use_case: StubCreatePaymentUseCase) -> FastAPI:
    app = FastAPI(title="highload-payments-test-api")
    app.state.create_payment_use_case = stub_create_payment_use_case
    setup_controllers(app)
    return app


@pytest.fixture
def api_client(api_app: FastAPI) -> TestClient:
    return TestClient(api_app)


@pytest.fixture
def integration_api_app(
    db_session_factory: async_sessionmaker[AsyncSession],
    test_db_config: DbConfig,
) -> FastAPI:
    settings = ApiSettings(
        common=CommonConfig(
            app_name="highload-payments-test",
            environment="test",
            log_level="INFO",
        ),
        db=test_db_config,
        nats=NatsConfig(
            servers=("nats://127.0.0.1:4222",),
            stream_name="payments",
            outbox_subject="payments.outbox",
            consumer_durable="dispatcher-webhooks",
        ),
        api=ApiConfig(host="127.0.0.1", port=5000),
    )
    app = FastAPI(title="highload-payments-integration-api")
    app.state.create_payment_use_case = build_create_payment_use_case(
        settings,
        db_session_factory,
    )
    setup_controllers(app)
    return app


@pytest.fixture
def integration_api_client(integration_api_app: FastAPI) -> TestClient:
    return TestClient(integration_api_app)
