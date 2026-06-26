"""Nagad Payment API client.

Sandbox: http://sandbox.mynagad.com:10080/merchant-api
Live:    https://api.mynagad.com

Nagad uses RSA encryption for sensitive data.
Requires: pip install cryptography
"""
from __future__ import annotations

import base64
import json
import time
import uuid

import httpx
from app.core.config import get_settings

settings = get_settings()

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False


def _rsa_encrypt(data: str, public_key_pem: str) -> str:
    if not _HAS_CRYPTO:
        raise RuntimeError("pip install cryptography required for Nagad payments")
    pub_key = serialization.load_pem_public_key(public_key_pem.encode())
    encrypted = pub_key.encrypt(data.encode(), asym_padding.PKCS1v15())  # type: ignore[attr-defined]
    return base64.b64encode(encrypted).decode()


def _rsa_sign(data: str, private_key_pem: str) -> str:
    if not _HAS_CRYPTO:
        raise RuntimeError("pip install cryptography required for Nagad payments")
    priv_key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
    signature = priv_key.sign(data.encode(), asym_padding.PKCS1v15(), hashes.SHA256())  # type: ignore[attr-defined]
    return base64.b64encode(signature).decode()


class NagadClient:
    def _datetime_str(self) -> str:
        return time.strftime("%Y%m%d%H%M%S", time.gmtime())

    async def check_account(self) -> dict:
        """Check merchant account status (public endpoint, no crypto)."""
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{settings.nagad_base_url}/api/dfs/check-out/v1.0"
                f"/merchant-info/check-account/{settings.nagad_merchant_number}",
            )
            r.raise_for_status()
            return r.json()

    async def create_order(
        self,
        order_id: str,
        amount: float,
        product_name: str = "Order",
    ) -> dict:
        """Initiate a Nagad payment order. Returns redirect URL for buyer."""
        datetime_str = self._datetime_str()
        challenge = str(uuid.uuid4()).replace("-", "")

        sensitive = json.dumps({
            "merchantId": settings.nagad_merchant_id,
            "datetime": datetime_str,
            "orderId": order_id,
            "challenge": challenge,
        })
        encrypted_sensitive = _rsa_encrypt(sensitive, settings.nagad_public_key)
        signature = _rsa_sign(sensitive, settings.nagad_private_key)

        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{settings.nagad_base_url}/api/dfs/check-out/v1.0"
                f"/place-order/{settings.nagad_merchant_number}",
                headers={"Content-Type": "application/json", "X-KM-IP-V4": "127.0.0.1",
                         "X-KM-MC-Id": settings.nagad_merchant_id,
                         "X-KM-Client-Type": "PC_WEB", "X-KM-Api-Version": "v-0.2.0"},
                json={
                    "dateTime": datetime_str,
                    "orderId": order_id,
                    "sensitiveData": encrypted_sensitive,
                    "signature": signature,
                },
            )
            r.raise_for_status()
            data = r.json()

        if data.get("status") != "Success":
            raise Exception(f"Nagad place order failed: {data}")

        return await self._complete_order(data, order_id, amount, product_name)

    async def _complete_order(
        self, place_order_response: dict, order_id: str, amount: float, product_name: str
    ) -> dict:
        payment_reference_id = place_order_response.get("paymentReferenceId", "")
        challenge = place_order_response.get("challenge", "")

        sensitive = json.dumps({
            "merchantId": settings.nagad_merchant_id,
            "orderId": order_id,
            "amount": f"{amount:.2f}",
            "currencyCode": "050",
            "challenge": challenge,
        })
        encrypted_sensitive = _rsa_encrypt(sensitive, settings.nagad_public_key)
        signature = _rsa_sign(sensitive, settings.nagad_private_key)

        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{settings.nagad_base_url}/api/dfs/check-out/v1.0"
                f"/complete/{settings.nagad_merchant_number}",
                headers={"Content-Type": "application/json", "X-KM-IP-V4": "127.0.0.1",
                         "X-KM-MC-Id": settings.nagad_merchant_id,
                         "X-KM-Client-Type": "PC_WEB", "X-KM-Api-Version": "v-0.2.0"},
                json={
                    "sensitiveData": encrypted_sensitive,
                    "signature": signature,
                    "paymentRefId": payment_reference_id,
                    "merchantCallbackURL": f"{settings.storefront_base_url}/checkout/callback",
                    "additionalMerchantInfo": {
                        "productName": product_name,
                        "productCount": 1,
                    },
                },
            )
            r.raise_for_status()
            data = r.json()

        if data.get("status") != "Success":
            raise Exception(f"Nagad complete order failed: {data}")

        return {
            "call_back_url": data.get("callBackUrl", ""),
            "payment_reference_id": payment_reference_id,
            "status": "pending",
        }

    async def verify_payment(self, payment_reference_id: str) -> dict:
        """Verify payment status after Nagad callback."""
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{settings.nagad_base_url}/api/dfs/verify/payment/{payment_reference_id}",
                headers={"X-KM-MC-Id": settings.nagad_merchant_id,
                         "X-KM-Client-Type": "PC_WEB", "X-KM-Api-Version": "v-0.2.0"},
            )
            r.raise_for_status()
            return r.json()
