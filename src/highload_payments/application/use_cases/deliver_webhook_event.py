from dataclasses import dataclass
from datetime import UTC, datetime

from highload_payments.application.dto.commands import DeliverWebhookCommand
from highload_payments.application.policies.retry import ExponentialBackoffPolicy
from highload_payments.application.ports.delivery import WebhookSenderPort
from highload_payments.application.ports.uow import UnitOfWork
from highload_payments.domain.entities.webhook_delivery_state import (
    WebhookDeliveryState,
)
from highload_payments.domain.value_objects.webhook_delivery_status import (
    WebhookDeliveryStatus,
)


@dataclass(frozen=True, slots=True)
class DeliveryOutcome:
    delivered_count: int
    pending_count: int
    retry_count: int
    terminal_failures: int
    next_retry_delay_seconds: int | None

    @property
    def should_retry(self) -> bool:
        return self.pending_count > 0 or self.retry_count > 0


class DeliverWebhookEventUseCase:
    def __init__(
        self,
        uow: UnitOfWork,
        sender: WebhookSenderPort,
        retry_policy: ExponentialBackoffPolicy,
        max_attempts: int,
    ) -> None:
        self._uow = uow
        self._sender = sender
        self._retry_policy = retry_policy
        self._max_attempts = max_attempts

    async def execute(self, command: DeliverWebhookCommand) -> DeliveryOutcome:
        delivered_count = 0
        async with self._uow as uow:
            endpoints = await uow.webhook_endpoints.get_by_account(command.account_id)
            endpoint_ids = [endpoint.endpoint_id for endpoint in endpoints]
            endpoint_by_id = {endpoint.endpoint_id: endpoint for endpoint in endpoints}

            await uow.webhook_delivery_states.initialize_for_event(
                event_id=command.event_id,
                endpoint_ids=endpoint_ids,
            )

            current_states = await uow.webhook_delivery_states.get_by_event(command.event_id)
            due_states = await uow.webhook_delivery_states.get_due_by_event(
                event_id=command.event_id,
                size=max(len(current_states), 1),
            )

            for state in due_states:
                endpoint = endpoint_by_id.get(state.endpoint_id)
                if endpoint is None:
                    state.mark_terminal_failure(reason="webhook endpoint not found")
                    await uow.webhook_delivery_states.update(state)
                    continue

                result = await self._sender.send(
                    endpoint=endpoint,
                    event_type=command.event_type,
                    payload=command.payload,
                )
                if result.delivered:
                    delivered_count += 1
                    state.mark_succeeded(status_code=result.status_code)
                elif result.retryable and state.attempts + 1 < self._max_attempts:
                    delay_seconds = self._retry_policy.next_delay(state.attempts + 1)
                    state.schedule_retry(
                        delay_seconds=delay_seconds,
                        reason=result.detail,
                        status_code=result.status_code,
                    )
                else:
                    state.mark_terminal_failure(
                        reason=result.detail,
                        status_code=result.status_code,
                    )
                await uow.webhook_delivery_states.update(state)

            states = await uow.webhook_delivery_states.get_by_event(command.event_id)
            await uow.commit()

        pending_count = sum(
            1 for state in states if state.status == WebhookDeliveryStatus.PENDING
        )
        retry_states = [
            state for state in states if state.status == WebhookDeliveryStatus.RETRY
        ]
        terminal_failures = sum(
            1
            for state in states
            if state.status == WebhookDeliveryStatus.FAILED_TERMINAL
        )
        return DeliveryOutcome(
            delivered_count=delivered_count,
            pending_count=pending_count,
            retry_count=len(retry_states),
            terminal_failures=terminal_failures,
            next_retry_delay_seconds=_next_retry_delay_seconds(retry_states),
        )


def _next_retry_delay_seconds(
    retry_states: list[WebhookDeliveryState],
) -> int | None:
    if not retry_states:
        return None

    now = datetime.now(tz=UTC)
    due_at = min(
        (
            state.next_retry_at
            for state in retry_states
            if state.next_retry_at is not None
        ),
        default=None,
    )
    if due_at is None:
        return 0

    seconds = int((due_at - now).total_seconds())
    return max(seconds, 0)
