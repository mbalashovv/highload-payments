from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from highload_payments.infrastructure.db.models.base import BaseModel


class OutboxEventModel(BaseModel):
    __tablename__ = "outbox_events"

    event_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    aggregate_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
