from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class WebhookEndpoint:
    endpoint_id: UUID
    account_id: UUID
    url: str
    secret: str

