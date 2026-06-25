"""Payment integration — SSLCommerz, bKash, Nagad, COD (all mock until real keys set)."""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PaymentIntent:
    payment_id: str
    provider: str
    status: str  # pending | paid | failed | refunded | partial
    amount: float
    currency: str
    payment_url: str
    created_at: str


@dataclass
class PaymentStatus:
    payment_id: str
    provider: str
    status: str
    amount: float
    paid_amount: float
    is_paid: bool
    is_refunded: bool
    transaction_id: str
    checked_at: str


class PaymentProvider(ABC):
    name: str
    display_name: str

    def is_configured(self) -> bool:
        return False

    @abstractmethod
    async def create_intent(self, order_id: str, amount: float) -> PaymentIntent: ...

    @abstractmethod
    async def get_status(self, payment_id: str) -> PaymentStatus: ...

    async def refund(self, payment_id: str, amount: float) -> dict:
        return {"success": True, "refund_id": f"REF-{uuid.uuid4().hex[:8].upper()}", "amount": amount, "mode": "mock"}

    async def test_connection(self) -> dict:
        return {"success": True, "mode": "mock", "message": "Mock connection OK"}


def _pid(prefix: str, order_id: str) -> str:
    try:
        seed = int(uuid.UUID(order_id).int % 9_000_000) + 1_000_000
    except (ValueError, AttributeError):
        seed = abs(hash(order_id)) % 9_000_000 + 1_000_000
    return f"{prefix}{seed}"


class SSLCommerzProvider(PaymentProvider):
    name = "sslcommerz"
    display_name = "SSLCommerz"

    def __init__(self, store_id: str = "", store_password: str = "") -> None:
        self._ok = bool(store_id and store_password)

    def is_configured(self) -> bool:
        return self._ok

    async def create_intent(self, order_id: str, amount: float) -> PaymentIntent:
        pid = _pid("SSL-", order_id)
        return PaymentIntent(payment_id=pid, provider="sslcommerz", status="pending",
                             amount=amount, currency="BDT",
                             payment_url=f"https://sandbox.sslcommerz.com/pay/{pid}",
                             created_at=datetime.utcnow().isoformat())

    async def get_status(self, payment_id: str) -> PaymentStatus:
        return PaymentStatus(payment_id=payment_id, provider="sslcommerz",
                             status="pending", amount=0, paid_amount=0,
                             is_paid=False, is_refunded=False,
                             transaction_id=f"TXN-{payment_id}", checked_at=datetime.utcnow().isoformat())


class BkashProvider(PaymentProvider):
    name = "bkash"
    display_name = "bKash"

    def __init__(self, app_key: str = "", app_secret: str = "") -> None:
        self._ok = bool(app_key and app_secret)

    def is_configured(self) -> bool:
        return self._ok

    async def create_intent(self, order_id: str, amount: float) -> PaymentIntent:
        pid = _pid("BKS-", order_id)
        return PaymentIntent(payment_id=pid, provider="bkash", status="pending",
                             amount=amount, currency="BDT",
                             payment_url=f"https://checkout.bkash.com/{pid}",
                             created_at=datetime.utcnow().isoformat())

    async def get_status(self, payment_id: str) -> PaymentStatus:
        return PaymentStatus(payment_id=payment_id, provider="bkash",
                             status="pending", amount=0, paid_amount=0,
                             is_paid=False, is_refunded=False,
                             transaction_id=f"BKT-{payment_id}", checked_at=datetime.utcnow().isoformat())


class NagadProvider(PaymentProvider):
    name = "nagad"
    display_name = "Nagad"

    def __init__(self, merchant_id: str = "", merchant_number: str = "") -> None:
        self._ok = bool(merchant_id and merchant_number)

    def is_configured(self) -> bool:
        return self._ok

    async def create_intent(self, order_id: str, amount: float) -> PaymentIntent:
        pid = _pid("NGD-", order_id)
        return PaymentIntent(payment_id=pid, provider="nagad", status="pending",
                             amount=amount, currency="BDT",
                             payment_url=f"https://api.nagad.com/checkout/{pid}",
                             created_at=datetime.utcnow().isoformat())

    async def get_status(self, payment_id: str) -> PaymentStatus:
        return PaymentStatus(payment_id=payment_id, provider="nagad",
                             status="pending", amount=0, paid_amount=0,
                             is_paid=False, is_refunded=False,
                             transaction_id=f"NGT-{payment_id}", checked_at=datetime.utcnow().isoformat())


class CODProvider(PaymentProvider):
    name = "cod"
    display_name = "Cash on Delivery"

    def is_configured(self) -> bool:
        return True

    async def create_intent(self, order_id: str, amount: float) -> PaymentIntent:
        pid = f"COD-{uuid.uuid4().hex[:8].upper()}"
        return PaymentIntent(payment_id=pid, provider="cod", status="cod_pending",
                             amount=amount, currency="BDT", payment_url="",
                             created_at=datetime.utcnow().isoformat())

    async def get_status(self, payment_id: str) -> PaymentStatus:
        return PaymentStatus(payment_id=payment_id, provider="cod",
                             status="cod_pending", amount=0, paid_amount=0,
                             is_paid=False, is_refunded=False,
                             transaction_id=payment_id, checked_at=datetime.utcnow().isoformat())


_REGISTRY: dict[str, PaymentProvider] = {
    "sslcommerz": SSLCommerzProvider(),
    "bkash":      BkashProvider(),
    "nagad":      NagadProvider(),
    "cod":        CODProvider(),
}


def get_payment(name: str) -> PaymentProvider:
    return _REGISTRY.get(name, _REGISTRY["cod"])


def payment_status_list() -> list[dict]:
    return [
        {
            "name": p.name, "display_name": p.display_name,
            "is_configured": p.is_configured(), "mode": "real" if p.is_configured() else "mock",
        }
        for p in _REGISTRY.values()
    ]
