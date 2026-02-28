from uuid import UUID

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from highload_payments.infrastructure.db.models.base import BaseModel


class WebhookEndpointModel(BaseModel):
    __tablename__ = "webhook_endpoints"

    endpoint_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    secret: Mapped[str] = mapped_column(String(512), nullable=False)
