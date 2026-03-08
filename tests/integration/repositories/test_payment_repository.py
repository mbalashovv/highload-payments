from __future__ import annotations

from highload_payments.infrastructure.db.repositories.payment import (
    SqlAlchemyPaymentRepository,
)
from tests.factories import make_payment


async def test_payment_repository_add_and_get(db_session) -> None:
    payment = make_payment()
    repository = SqlAlchemyPaymentRepository(db_session)

    await repository.add(payment)
    await db_session.commit()

    loaded = await repository.get(payment.payment_id)

    assert loaded is not None
    assert loaded.payment_id == payment.payment_id
    assert loaded.account_id == payment.account_id
    assert loaded.money.amount_minor == payment.money.amount_minor
    assert loaded.money.currency == payment.money.currency

