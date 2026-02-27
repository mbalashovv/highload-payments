from highload_payments.application.dto.commands import DeliverWebhookCommand
from highload_payments.application.ports.delivery import WebhookSenderPort
from highload_payments.application.ports.uow import UnitOfWork


class DeliverWebhookEventUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        sender: WebhookSenderPort,
    ) -> None:
        self._uow = uow
        self._sender = sender

    async def execute(self, command: DeliverWebhookCommand) -> int:
        delivered_count = 0
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
            await uow.commit()
        return delivered_count

