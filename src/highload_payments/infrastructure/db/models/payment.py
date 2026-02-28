from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from highload_payments.infrastructure.db.models.base import BaseModel


class PaymentModel(BaseModel):
    __tablename__ = "payments"

    payment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
