"""bKash Tokenized Checkout API client.

Sandbox: https://tokenized.sandbox.bka.sh/v1.2.0-beta
Live:    https://tokenized.pay.bka.sh/v1.2.0-beta

Docs: https://developer.bka.sh/docs/tokenized-checkout
"""
from __future__ import annotations

import time

import httpx
from app.core.config import get_settings

settings = get_settings()

_token_cache: dict = {}


class BkashClient:
    async def _get_token(self) -> str:
        now = time.time()
        if _token_cache.get("expires_at", 0) > now:
            return _token_cache["token"]

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"{settings.bkash_base_url}/checkout/token/grant",
                headers={
                    "username": settings.bkash_username,
                    "password": settings.bkash_password,
                    "Content-Type": "application/json",
                },
                json={
                    "app_key": settings.bkash_app_key,
                    "app_secret": settings.bkash_app_secret,
                },
            )
            r.raise_for_status()
            data = r.json()

        token = data.get("id_token", "")
        if not token:
            raise Exception(f"bKash auth failed: {data}")
        _token_cache["token"] = token
        _token_cache["expires_at"] = now + 3500
        return token

    def _auth_headers(self, token: str) -> dict:
        return {
            "Authorization": token,
            "X-APP-Key": settings.bkash_app_key,
            "Content-Type": "application/json",
        }

    async def create_payment(
        self,
        merchant_invoice_number: str,
        amount: float,
        callback_url: str,
        payer_reference: str = "",
        currency: str = "BDT",
        intent: str = "sale",
    ) -> dict:
        """Create a tokenized checkout payment and return bKash payment URL."""
        token = await self._get_token()
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{settings.bkash_base_url}/checkout/create",
                headers=self._auth_headers(token),
                json={
                    "mode": "0011",
                    "payerReference": payer_reference or merchant_invoice_number,
                    "callbackURL": callback_url,
                    "merchantAssociationInfo": "SellerMate",
                    "amount": f"{amount:.2f}",
                    "currency": currency,
                    "intent": intent,
                    "merchantInvoiceNumber": merchant_invoice_number,
                },
            )
            r.raise_for_status()
            data = r.json()

        if data.get("statusCode") == "0000":
            return {
                "payment_id": data["paymentID"],
                "bkash_url": data["bkashURL"],
                "status": "pending",
            }
        raise Exception(f"bKash create payment failed: {data.get('statusMessage', data)}")

    async def execute_payment(self, payment_id: str) -> dict:
        """Execute payment after buyer completes bKash flow (called in callback)."""
        token = await self._get_token()
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{settings.bkash_base_url}/checkout/execute/{payment_id}",
                headers=self._auth_headers(token),
            )
            r.raise_for_status()
            return r.json()

    async def query_payment(self, payment_id: str) -> dict:
        """Query payment status by paymentID."""
        token = await self._get_token()
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{settings.bkash_base_url}/checkout/payment/{payment_id}",
                headers=self._auth_headers(token),
            )
            r.raise_for_status()
            return r.json()

    async def search_transaction(self, trx_id: str) -> dict:
        """Search by bKash transaction ID (TrxID)."""
        token = await self._get_token()
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{settings.bkash_base_url}/checkout/transaction/status/{trx_id}",
                headers=self._auth_headers(token),
            )
            r.raise_for_status()
            return r.json()

    async def refund(self, payment_id: str, amount: float, trx_id: str, reason: str = "") -> dict:
        """Initiate refund for a completed bKash payment."""
        token = await self._get_token()
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{settings.bkash_base_url}/checkout/payment/refund/{payment_id}",
                headers=self._auth_headers(token),
                json={
                    "amount": f"{amount:.2f}",
                    "trxID": trx_id,
                    "sku": reason or "refund",
                    "reason": reason or "Customer requested refund",
                },
            )
            r.raise_for_status()
            return r.json()
