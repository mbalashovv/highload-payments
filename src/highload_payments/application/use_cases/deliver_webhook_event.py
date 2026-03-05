from dataclasses import dataclass

from highload_payments.application.dto.commands import DeliverWebhookCommand
from highload_payments.application.ports.delivery import WebhookSenderPort
from highload_payments.application.ports.uow import UnitOfWork


@dataclass(frozen=True, slots=True)
class DeliveryOutcome:
    delivered_count: int
    retryable_failures: int
    non_retryable_failures: int

    @property
    def should_retry(self) -> bool:
        return self.retryable_failures > 0


class DeliverWebhookEventUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        sender: WebhookSenderPort,
    ) -> None:
        self._uow = uow
        self._sender = sender

    async def execute(self, command: DeliverWebhookCommand) -> DeliveryOutcome:
        delivered_count = 0
        retryable_failures = 0
        non_retryable_failures = 0
        async with self._uow as uow:
            endpoints = await uow.webhook_endpoints.get_by_account(command.account_id)
            for endpoint in endpoints:
                result = await self._sender.send(
                    endpoint=endpoint,
                    event_type=command.event_type,
                    payload=command.payload,
                )
                if result.delivered:
                    delivered_count += 1
                elif result.retryable:
                    retryable_failures += 1
                else:
                    non_retryable_failures += 1
            await uow.commit()
        return DeliveryOutcome(
            delivered_count=delivered_count,
            retryable_failures=retryable_failures,
            non_retryable_failures=non_retryable_failures,
        )
