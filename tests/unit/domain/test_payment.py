from __future__ import annotations

import pytest

from highload_payments.domain.errors import InvalidPaymentTransitionError
from highload_payments.domain.value_objects.payment_status import PaymentStatus
from tests.factories import make_money, make_payment


def test_create_sets_created_status_and_timestamps() -> None:
    payment = make_payment()

    assert payment.status == PaymentStatus.CREATED
    assert payment.created_at == payment.updated_at


def test_mark_processing_moves_payment_to_processing() -> None:
    payment = make_payment()

    payment.mark_processing()

    assert payment.status == PaymentStatus.PROCESSING
    assert payment.updated_at >= payment.created_at


def test_mark_processing_from_non_created_raises() -> None:
    payment = make_payment()
    payment.mark_succeeded()

    with pytest.raises(
        InvalidPaymentTransitionError,
        match="processing is allowed only from created",
    ):
        payment.mark_processing()


@pytest.mark.parametrize("initial_status", [PaymentStatus.CREATED, PaymentStatus.PROCESSING])
def test_mark_succeeded_allows_created_and_processing(
    initial_status: PaymentStatus,
) -> None:
    payment = make_payment()
    if initial_status == PaymentStatus.PROCESSING:
        payment.mark_processing()

    payment.mark_succeeded()

    assert payment.status == PaymentStatus.SUCCEEDED


@pytest.mark.parametrize("initial_status", [PaymentStatus.SUCCEEDED, PaymentStatus.FAILED])
def test_mark_succeeded_from_invalid_state_raises(
    initial_status: PaymentStatus,
) -> None:
    payment = make_payment()
    if initial_status == PaymentStatus.SUCCEEDED:
        payment.mark_succeeded()
    else:
        payment.mark_failed()

    with pytest.raises(
        InvalidPaymentTransitionError,
        match="succeeded is not allowed from this state",
    ):
        payment.mark_succeeded()


@pytest.mark.parametrize("setup_transition", ["created", "processing"])
def test_mark_failed_allows_non_terminal_states(setup_transition: str) -> None:
    payment = make_payment()
    if setup_transition == "processing":
        payment.mark_processing()

    payment.mark_failed()

    assert payment.status == PaymentStatus.FAILED


@pytest.mark.parametrize("setup_transition", ["succeeded", "failed"])
def test_mark_failed_from_terminal_state_raises(setup_transition: str) -> None:
    payment = make_payment()
    if setup_transition == "succeeded":
        payment.mark_succeeded()
    else:
        payment.mark_failed()

    with pytest.raises(
        InvalidPaymentTransitionError,
        match="failed is not allowed from terminal state",
    ):
        payment.mark_failed()


def test_money_rejects_negative_amount() -> None:
    with pytest.raises(ValueError, match="amount_minor must be >= 0"):
        make_money(amount_minor=-1)


def test_money_rejects_empty_currency() -> None:
    with pytest.raises(ValueError, match="currency must not be empty"):
        make_money(currency="")
