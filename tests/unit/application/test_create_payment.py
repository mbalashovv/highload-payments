from __future__ import annotations

from highload_payments.application.use_cases.create_payment import CreatePaymentUseCase
from highload_payments.domain.value_objects.payment_status import PaymentStatus
from tests.factories import make_create_payment_command, make_payment


async def test_create_payment_persists_payment_and_outbox(
    fake_uow,
    in_memory_idempotency_store,
    sequential_id_generator,
) -> None:
    use_case = CreatePaymentUseCase(
        uow=fake_uow,
        idempotency_store=in_memory_idempotency_store,
        id_generator=sequential_id_generator,
    )
    command = make_create_payment_command()

    result = await use_case.execute(command)

    stored_payment = fake_uow.payments.items[result.payment_id]
    outbox_event = next(iter(fake_uow.outbox.items.values()))

    assert result.payment_id == stored_payment.payment_id
    assert result.status == PaymentStatus.CREATED
    assert result.duplicated is False
    assert stored_payment.account_id == command.account_id
    assert outbox_event.aggregate_id == stored_payment.payment_id
    assert outbox_event.event_type == "payment.created"
    assert fake_uow.commit_calls == 1


async def test_create_payment_returns_existing_result_for_same_idempotency_key(
    fake_uow,
    in_memory_idempotency_store,
    sequential_id_generator,
) -> None:
    command = make_create_payment_command(idempotency_key="same-key")
    existing_payment = make_payment(account_id=command.account_id)
    fake_uow.payments.items[existing_payment.payment_id] = existing_payment
    await in_memory_idempotency_store.save_payment_id(
        f"{command.account_id}:{command.idempotency_key}",
        existing_payment.payment_id,
    )
    use_case = CreatePaymentUseCase(
        uow=fake_uow,
        idempotency_store=in_memory_idempotency_store,
        id_generator=sequential_id_generator,
    )

    result = await use_case.execute(command)

    assert result.payment_id == existing_payment.payment_id
    assert result.status == existing_payment.status
    assert result.duplicated is True
    assert len(fake_uow.outbox.items) == 0
    assert fake_uow.commit_calls == 0

