from uuid import UUID

from pydantic import BaseModel, Field


class CreatePaymentRequest(BaseModel):
    account_id: UUID
    amount_minor: int = Field(ge=0)
    currency: str = Field(min_length=1, max_length=16)
    idempotency_key: str = Field(min_length=1, max_length=128)


class CreatePaymentResponse(BaseModel):
    payment_id: UUID
    status: str
    duplicated: bool
