from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from highload_payments.application.use_cases.create_payment import CreatePaymentUseCase
from highload_payments.infrastructure.db.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork
from highload_payments.infrastructure.idempotency.in_memory_store import InMemoryIdempotencyStore
from highload_payments.infrastructure.settings import ApiSettings
from highload_payments.infrastructure.uuid_generator import UUID4Generator


def build_create_payment_use_case(
    _settings: ApiSettings,
    session_factory: async_sessionmaker[AsyncSession],
) -> CreatePaymentUseCase:
    return CreatePaymentUseCase(
        uow=SqlAlchemyUnitOfWork(session_factory=session_factory),
        idempotency_store=InMemoryIdempotencyStore(),
        id_generator=UUID4Generator(),
    )
