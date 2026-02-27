from dataclasses import dataclass
import random


@dataclass(frozen=True, slots=True)
class ExponentialBackoffPolicy:
    base_seconds: int = 1
    max_seconds: int = 60
    jitter_seconds: float = 0.25

    def next_delay(self, attempt: int) -> int:
        raw = min(self.max_seconds, self.base_seconds * (2 ** max(attempt - 1, 0)))
        jitter = raw * random.uniform(0.0, self.jitter_seconds)
        return int(raw + jitter)

