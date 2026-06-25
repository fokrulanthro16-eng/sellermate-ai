# Import all models here so Alembic autogenerate can detect them.
from app.models.merchant import Merchant  # noqa: F401
from app.models.product import Product, ProductVariant  # noqa: F401
from app.models.inventory import InventoryLog  # noqa: F401
from app.models.customer import Customer  # noqa: F401
from app.models.order import Order, OrderItem, OrderStatusHistory  # noqa: F401
from app.models.assistant import Conversation, Message  # noqa: F401
from app.models.hermit import HermitInsight  # noqa: F401
from app.models.strategic_insight import StrategicInsight  # noqa: F401
from app.models.review import Review  # noqa: F401
from app.models.campaign import Campaign  # noqa: F401
from app.models.integration_setting import IntegrationSettings  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.webhook_event import WebhookEvent  # noqa: F401
from app.models.background_job import BackgroundJob  # noqa: F401

__all__ = [
    "Merchant",
    "Product",
    "ProductVariant",
    "InventoryLog",
    "Customer",
    "Order",
    "OrderItem",
    "OrderStatusHistory",
    "Conversation",
    "Message",
    "HermitInsight",
    "StrategicInsight",
    "Review",
    "Campaign",
    "IntegrationSettings",
    "AuditLog",
    "WebhookEvent",
    "BackgroundJob",
]
