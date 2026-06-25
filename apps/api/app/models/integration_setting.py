import uuid

from sqlalchemy import JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin

_DEFAULT_CONFIG: dict = {
    "courier":      {"active_provider": "manual", "pathao": {}, "steadfast": {}, "redx": {}},
    "payment":      {"active_provider": "cod",    "sslcommerz": {}, "bkash": {}, "nagad": {}},
    "marketplace":  {"facebook": {}, "daraz": {}, "shopify": {}},
    "notification": {"email": {}, "sms": {}, "whatsapp": {}},
}


class IntegrationSettings(Base, TimestampMixin):
    __tablename__ = "integration_settings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    merchant_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    config_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=lambda: dict(_DEFAULT_CONFIG))

    __table_args__ = (UniqueConstraint("merchant_id", name="uq_integration_settings_merchant"),)
