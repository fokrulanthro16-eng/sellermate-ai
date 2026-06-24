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
]
