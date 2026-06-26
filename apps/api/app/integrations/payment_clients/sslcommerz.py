"""SSLCommerz payment gateway client.

Sandbox: https://sandbox.sslcommerz.com
Live:    https://securepay.sslcommerz.com
"""
from __future__ import annotations

import httpx
from app.core.config import get_settings

settings = get_settings()


class SSLCommerzClient:
    async def init_payment(
        self,
        tran_id: str,
        amount: float,
        customer_name: str,
        customer_phone: str,
        customer_address: str,
        product_name: str,
        success_url: str,
        fail_url: str,
        cancel_url: str,
        customer_email: str = "customer@example.com",
        ipn_url: str = "",
        currency: str = "BDT",
        product_category: str = "clothing",
    ) -> dict:
        """Initiate payment and return the gateway page URL."""
        data = {
            "store_id": settings.sslcommerz_store_id,
            "store_passwd": settings.sslcommerz_store_password,
            "total_amount": f"{amount:.2f}",
            "currency": currency,
            "tran_id": tran_id,
            "success_url": success_url,
            "fail_url": fail_url,
            "cancel_url": cancel_url,
            "ipn_url": ipn_url or success_url,
            "product_category": product_category,
            "product_name": product_name[:255],
            "cus_name": customer_name,
            "cus_email": customer_email,
            "cus_phone": customer_phone,
            "cus_add1": customer_address[:120],
            "cus_city": "Dhaka",
            "cus_country": "Bangladesh",
            "ship_name": customer_name,
            "ship_add1": customer_address[:120],
            "ship_city": "Dhaka",
            "ship_country": "Bangladesh",
            "shipping_method": "NO",
            "product_profile": "general",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{settings.sslcommerz_base_url}/gwprocess/v4/api.php",
                data=data,
            )
            r.raise_for_status()
            result = r.json()

        if result.get("status") == "SUCCESS":
            return {
                "gateway_url": result["GatewayPageURL"],
                "session_key": result.get("sessionkey", ""),
                "status": "pending",
                "tran_id": tran_id,
            }
        raise Exception(f"SSLCommerz init failed: {result.get('failedreason', result)}")

    async def validate_ipn(self, val_id: str) -> dict:
        """Validate payment notification from SSLCommerz IPN callback."""
        params = {
            "store_id": settings.sslcommerz_store_id,
            "store_passwd": settings.sslcommerz_store_password,
            "val_id": val_id,
            "format": "json",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{settings.sslcommerz_base_url}/validator/api/validationserverAPI.php",
                params=params,
            )
            r.raise_for_status()
            return r.json()

    async def transaction_status(self, tran_id: str) -> dict:
        """Query transaction status by merchant transaction ID."""
        params = {
            "store_id": settings.sslcommerz_store_id,
            "store_passwd": settings.sslcommerz_store_password,
            "tran_id": tran_id,
            "format": "json",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{settings.sslcommerz_base_url}/validator/api/merchantTransIDvalidationAPI.php",
                params=params,
            )
            r.raise_for_status()
            return r.json()

    async def refund(self, bank_tran_id: str, amount: float, reason: str = "") -> dict:
        """Initiate refund for a completed transaction."""
        data = {
            "store_id": settings.sslcommerz_store_id,
            "store_passwd": settings.sslcommerz_store_password,
            "bank_tran_id": bank_tran_id,
            "refund_amount": f"{amount:.2f}",
            "refund_remarks": reason or "Customer requested refund",
            "format": "json",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{settings.sslcommerz_base_url}/validator/api/merchantTransIDvalidationAPI.php",
                data=data,
            )
            r.raise_for_status()
            return r.json()
