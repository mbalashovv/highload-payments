from __future__ import annotations

from uuid import UUID, uuid4

from highload_payments.application.dto.commands import CreatePaymentCommand
from highload_payments.domain.entities.payment import Payment
from highload_payments.domain.value_objects.money import Money


def make_money(
    *,
    amount_minor: int = 1500,
    currency: str = "USD",
) -> Money:
    return Money(amount_minor=amount_minor, currency=currency)


def make_payment(
    *,
    payment_id: UUID | None = None,
    account_id: UUID | None = None,
    amount_minor: int = 1500,
    currency: str = "USD",
) -> Payment:
    return Payment.create(
        payment_id=payment_id or uuid4(),
        account_id=account_id or uuid4(),
        money=make_money(amount_minor=amount_minor, currency=currency),
    )


def make_create_payment_command(
    *,
    account_id: UUID | None = None,
    amount_minor: int = 1500,
    currency: str = "USD",
    idempotency_key: str = "test-idempotency-key",
) -> CreatePaymentCommand:
    return CreatePaymentCommand(
        account_id=account_id or uuid4(),
        amount_minor=amount_minor,
        currency=currency,
        idempotency_key=idempotency_key,
    )
