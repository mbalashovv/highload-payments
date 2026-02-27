from highload_payments.application.ports.messaging import EventPublisherPort
from highload_payments.application.ports.uow import UnitOfWork
from highload_payments.application.policies.retry import ExponentialBackoffPolicy


class PublishOutboxBatchUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        publisher: EventPublisherPort,
        retry_policy: ExponentialBackoffPolicy,
        max_attempts: int = 10,
    ) -> None:
        self._uow = uow
        self._publisher = publisher
        self._retry_policy = retry_policy
        self._max_attempts = max_attempts

    async def execute(self, batch_size: int) -> int:
        processed = 0
        async with self._uow as uow:
            events = await uow.outbox.claim_batch(batch_size)
            for event in events:
                try:
                    await self._publisher.publish(event)
                except Exception as exc:
                    if event.attempts + 1 >= self._max_attempts:
                        event.mark_dead(reason=str(exc))
                    else:
                        delay = self._retry_policy.next_delay(event.attempts + 1)
                        event.schedule_retry(delay_seconds=delay, reason=str(exc))
                else:
                    event.mark_published()
                await uow.outbox.update(event)
                processed += 1
            await uow.commit()
        return processed

