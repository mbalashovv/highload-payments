from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Money:
    amount_minor: int
    currency: str

    def __post_init__(self) -> None:
        if self.amount_minor < 0:
            raise ValueError("amount_minor must be >= 0")
        if not self.currency:
            raise ValueError("currency must not be empty")

