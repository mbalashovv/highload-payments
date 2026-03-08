from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from highload_payments.domain.entities.outbox_event import OutboxEvent


@dataclass(slots=True)
class RecordingPublisher:
    published_events: list[OutboxEvent] = field(default_factory=list)
    failures_remaining: int = 0

    async def publish(self, event: OutboxEvent) -> None:
        if self.failures_remaining > 0:
            self.failures_remaining -= 1
            raise RuntimeError("publisher failure")
        self.published_events.append(event)


@pytest.fixture
def recording_publisher() -> RecordingPublisher:
    return RecordingPublisher()
