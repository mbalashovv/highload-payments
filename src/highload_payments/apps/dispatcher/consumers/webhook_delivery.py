from highload_payments.application.dto.commands import DeliverWebhookCommand
from highload_payments.application.use_cases.deliver_webhook_event import (
    DeliverWebhookEventUseCase,
)


async def consume_event(
    use_case: DeliverWebhookEventUseCase,
    command: DeliverWebhookCommand,
) -> int:
    return await use_case.execute(command)

