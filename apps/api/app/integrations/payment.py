"""Payment integration — SSLCommerz, bKash, Nagad, COD.

Uses real API clients when credentials are configured in settings; falls back to mock.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from app.core.config import get_settings


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
    async def create_intent(self, order_id: str, amount: float, **kwargs) -> PaymentIntent: ...

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

    def __init__(self) -> None:
        s = get_settings()
        self._ok = bool(s.sslcommerz_store_id and s.sslcommerz_store_password)

    def is_configured(self) -> bool:
        return self._ok

    async def create_intent(self, order_id: str, amount: float, **kwargs) -> PaymentIntent:
        if self._ok:
            from app.integrations.payment_clients.sslcommerz import SSLCommerzClient
            s = get_settings()
            base = s.storefront_base_url or "https://sellermate.ai"
            result = await SSLCommerzClient().init_payment(
                tran_id=order_id,
                amount=amount,
                customer_name=kwargs.get("customer_name", "Customer"),
                customer_phone=kwargs.get("customer_phone", ""),
                customer_address=kwargs.get("customer_address", "Dhaka"),
                product_name=kwargs.get("product_name", "Order"),
                success_url=f"{base}/checkout/callback?provider=sslcommerz&status=success",
                fail_url=f"{base}/checkout/callback?provider=sslcommerz&status=fail",
                cancel_url=f"{base}/checkout/callback?provider=sslcommerz&status=cancel",
                customer_email=kwargs.get("customer_email", "customer@example.com"),
            )
            return PaymentIntent(
                payment_id=result["session_key"] or order_id,
                provider="sslcommerz", status="pending",
                amount=amount, currency="BDT",
                payment_url=result["gateway_url"],
                created_at=datetime.utcnow().isoformat(),
            )
        pid = _pid("SSL-", order_id)
        return PaymentIntent(payment_id=pid, provider="sslcommerz", status="pending",
                             amount=amount, currency="BDT",
                             payment_url=f"https://sandbox.sslcommerz.com/pay/{pid}",
                             created_at=datetime.utcnow().isoformat())

    async def get_status(self, payment_id: str) -> PaymentStatus:
        if self._ok and not payment_id.startswith("SSL-"):
            from app.integrations.payment_clients.sslcommerz import SSLCommerzClient
            try:
                result = await SSLCommerzClient().transaction_status(payment_id)
                is_paid = result.get("status") == "VALID"
                return PaymentStatus(
                    payment_id=payment_id, provider="sslcommerz",
                    status="paid" if is_paid else "pending",
                    amount=float(result.get("amount", 0)),
                    paid_amount=float(result.get("amount", 0)) if is_paid else 0,
                    is_paid=is_paid, is_refunded=False,
                    transaction_id=result.get("tran_id", payment_id),
                    checked_at=datetime.utcnow().isoformat(),
                )
            except Exception:
                pass
        return PaymentStatus(payment_id=payment_id, provider="sslcommerz",
                             status="pending", amount=0, paid_amount=0,
                             is_paid=False, is_refunded=False,
                             transaction_id=f"TXN-{payment_id}", checked_at=datetime.utcnow().isoformat())

    async def test_connection(self) -> dict:
        if self._ok:
            return {"success": True, "mode": "real", "message": "SSLCommerz credentials configured"}
        return {"success": True, "mode": "mock", "message": "Mock connection OK"}


class BkashProvider(PaymentProvider):
    name = "bkash"
    display_name = "bKash"

    def __init__(self) -> None:
        s = get_settings()
        self._ok = bool(s.bkash_app_key and s.bkash_app_secret
                        and s.bkash_username and s.bkash_password)

    def is_configured(self) -> bool:
        return self._ok

    async def create_intent(self, order_id: str, amount: float, **kwargs) -> PaymentIntent:
        if self._ok:
            from app.integrations.payment_clients.bkash import BkashClient
            s = get_settings()
            base = s.storefront_base_url or "https://sellermate.ai"
            result = await BkashClient().create_payment(
                merchant_invoice_number=order_id,
                amount=amount,
                callback_url=f"{base}/checkout/callback?provider=bkash",
                payer_reference=kwargs.get("customer_phone", order_id),
            )
            return PaymentIntent(
                payment_id=result["payment_id"],
                provider="bkash", status="pending",
                amount=amount, currency="BDT",
                payment_url=result["bkash_url"],
                created_at=datetime.utcnow().isoformat(),
            )
        pid = _pid("BKS-", order_id)
        return PaymentIntent(payment_id=pid, provider="bkash", status="pending",
                             amount=amount, currency="BDT",
                             payment_url=f"https://checkout.bkash.com/{pid}",
                             created_at=datetime.utcnow().isoformat())

    async def get_status(self, payment_id: str) -> PaymentStatus:
        if self._ok and not payment_id.startswith("BKS-"):
            from app.integrations.payment_clients.bkash import BkashClient
            try:
                result = await BkashClient().query_payment(payment_id)
                is_paid = result.get("transactionStatus") == "Completed"
                return PaymentStatus(
                    payment_id=payment_id, provider="bkash",
                    status="paid" if is_paid else result.get("transactionStatus", "pending").lower(),
                    amount=float(result.get("amount", 0)),
                    paid_amount=float(result.get("amount", 0)) if is_paid else 0,
                    is_paid=is_paid, is_refunded=False,
                    transaction_id=result.get("trxID", payment_id),
                    checked_at=datetime.utcnow().isoformat(),
                )
            except Exception:
                pass
        return PaymentStatus(payment_id=payment_id, provider="bkash",
                             status="pending", amount=0, paid_amount=0,
                             is_paid=False, is_refunded=False,
                             transaction_id=f"BKT-{payment_id}", checked_at=datetime.utcnow().isoformat())

    async def refund(self, payment_id: str, amount: float) -> dict:
        if self._ok and not payment_id.startswith("BKS-"):
            from app.integrations.payment_clients.bkash import BkashClient
            try:
                result = await BkashClient().refund(payment_id, amount, trx_id=payment_id)
                return {"success": True, "refund_id": result.get("refundTrxID", ""), "amount": amount, "mode": "real"}
            except Exception as exc:
                return {"success": False, "error": str(exc), "amount": amount, "mode": "real"}
        return {"success": True, "refund_id": f"REF-{uuid.uuid4().hex[:8].upper()}", "amount": amount, "mode": "mock"}

    async def test_connection(self) -> dict:
        if self._ok:
            from app.integrations.payment_clients.bkash import BkashClient
            try:
                await BkashClient()._get_token()
                return {"success": True, "mode": "real", "message": "bKash token obtained"}
            except Exception as exc:
                return {"success": False, "mode": "real", "error": str(exc)}
        return {"success": True, "mode": "mock", "message": "Mock connection OK"}


class NagadProvider(PaymentProvider):
    name = "nagad"
    display_name = "Nagad"

    def __init__(self) -> None:
        s = get_settings()
        self._ok = bool(s.nagad_merchant_id and s.nagad_merchant_number
                        and s.nagad_public_key and s.nagad_private_key)

    def is_configured(self) -> bool:
        return self._ok

    async def create_intent(self, order_id: str, amount: float, **kwargs) -> PaymentIntent:
        if self._ok:
            from app.integrations.payment_clients.nagad import NagadClient
            result = await NagadClient().create_order(order_id, amount,
                                                       product_name=kwargs.get("product_name", "Order"))
            return PaymentIntent(
                payment_id=result["payment_reference_id"],
                provider="nagad", status="pending",
                amount=amount, currency="BDT",
                payment_url=result["call_back_url"],
                created_at=datetime.utcnow().isoformat(),
            )
        pid = _pid("NGD-", order_id)
        return PaymentIntent(payment_id=pid, provider="nagad", status="pending",
                             amount=amount, currency="BDT",
                             payment_url=f"https://api.nagad.com/checkout/{pid}",
                             created_at=datetime.utcnow().isoformat())

    async def get_status(self, payment_id: str) -> PaymentStatus:
        if self._ok and not payment_id.startswith("NGD-"):
            from app.integrations.payment_clients.nagad import NagadClient
            try:
                result = await NagadClient().verify_payment(payment_id)
                is_paid = result.get("status") == "Success"
                return PaymentStatus(
                    payment_id=payment_id, provider="nagad",
                    status="paid" if is_paid else "pending",
                    amount=float(result.get("amount", 0)),
                    paid_amount=float(result.get("amount", 0)) if is_paid else 0,
                    is_paid=is_paid, is_refunded=False,
                    transaction_id=result.get("issuerPaymentReferenceNumber", payment_id),
                    checked_at=datetime.utcnow().isoformat(),
                )
            except Exception:
                pass
        return PaymentStatus(payment_id=payment_id, provider="nagad",
                             status="pending", amount=0, paid_amount=0,
                             is_paid=False, is_refunded=False,
                             transaction_id=f"NGT-{payment_id}", checked_at=datetime.utcnow().isoformat())

    async def test_connection(self) -> dict:
        if self._ok:
            from app.integrations.payment_clients.nagad import NagadClient
            try:
                result = await NagadClient().check_account()
                return {"success": True, "mode": "real", "account": result}
            except Exception as exc:
                return {"success": False, "mode": "real", "error": str(exc)}
        return {"success": True, "mode": "mock", "message": "Mock connection OK"}


class CODProvider(PaymentProvider):
    name = "cod"
    display_name = "Cash on Delivery"

    def is_configured(self) -> bool:
        return True

    async def create_intent(self, order_id: str, amount: float, **kwargs) -> PaymentIntent:
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
