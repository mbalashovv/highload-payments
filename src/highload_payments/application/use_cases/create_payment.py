from dataclasses import asdict

from highload_payments.application.dto.commands import CreatePaymentCommand
from highload_payments.application.dto.results import PaymentResult
from highload_payments.application.ports.idempotency import IdempotencyStorePort
from highload_payments.application.ports.uow import UnitOfWork
from highload_payments.domain.entities.outbox_event import OutboxEvent
from highload_payments.domain.entities.payment import Payment
from highload_payments.domain.events.payment_created import PaymentCreatedEvent
from highload_payments.domain.ports.id_generator import IdGenerator
from highload_payments.domain.value_objects.money import Money


class CreatePaymentUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        idempotency_store: IdempotencyStorePort,
        id_generator: IdGenerator,
    ) -> None:
        self._uow = uow
        self._idempotency_store = idempotency_store
        self._id_generator = id_generator

    async def execute(self, command: CreatePaymentCommand) -> PaymentResult:
        idem_key = f"{command.account_id}:{command.idempotency_key}"
        existing_payment_id = await self._idempotency_store.get_payment_id(idem_key)

        if existing_payment_id is not None:
            async with self._uow as uow:
                existing = await uow.payments.get(existing_payment_id)
                if existing is not None:
                    return PaymentResult(
                        payment_id=existing.payment_id,
                        status=existing.status,
                        duplicated=True,
                    )

        payment_id = self._id_generator.new()
        event_id = self._id_generator.new()

        payment = Payment.create(
            payment_id=payment_id,
            account_id=command.account_id,
            money=Money(amount_minor=command.amount_minor, currency=command.currency),
        )
        created_event = PaymentCreatedEvent(
            event_id=event_id,
            payment_id=payment.payment_id,
            account_id=payment.account_id,
            amount_minor=payment.money.amount_minor,
            currency=payment.money.currency,
        )
        outbox_event = OutboxEvent.create(
            event_id=created_event.event_id,
            aggregate_id=created_event.payment_id,
            event_type="payment.created",
            payload=asdict(created_event),
        )

        async with self._uow as uow:
            await uow.payments.add(payment)
            await uow.outbox.add(outbox_event)
            await uow.commit()

        await self._idempotency_store.save_payment_id(idem_key, payment_id)

        return PaymentResult(
            payment_id=payment.payment_id,
            status=payment.status,
            duplicated=False,
        )

