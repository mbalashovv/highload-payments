from highload_payments.application.use_cases.publish_outbox_batch import (
    PublishOutboxBatchUseCase,
)


async def publish_once(use_case: PublishOutboxBatchUseCase, batch_size: int) -> int:
    return await use_case.execute(batch_size=batch_size)

