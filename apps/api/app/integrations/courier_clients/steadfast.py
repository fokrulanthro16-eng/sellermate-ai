"""Steadfast courier API client — https://portal.steadfast.com.bd/public-api"""
from __future__ import annotations

import httpx
from app.core.config import get_settings

settings = get_settings()


class SteadfastClient:
    def _headers(self) -> dict:
        return {
            "X-API-Key": settings.steadfast_api_key,
            "X-SECRET-KEY": settings.steadfast_secret_key,
            "Content-Type": "application/json",
        }

    async def create_order(
        self,
        invoice: str,
        recipient_name: str,
        recipient_phone: str,
        recipient_address: str,
        cod_amount: float,
        note: str = "",
    ) -> dict:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{settings.steadfast_base_url}/api/v1/create_order",
                headers=self._headers(),
                json={
                    "invoice": invoice,
                    "recipient_name": recipient_name,
                    "recipient_phone": recipient_phone,
                    "recipient_address": recipient_address,
                    "cod_amount": cod_amount,
                    "note": note,
                },
            )
            r.raise_for_status()
            return r.json()

    async def bulk_create_orders(self, orders: list[dict]) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{settings.steadfast_base_url}/api/v1/create_order/bulk-order",
                headers=self._headers(),
                json={"data": orders},
            )
            r.raise_for_status()
            return r.json()

    async def track_by_consignment(self, consignment_id: str) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{settings.steadfast_base_url}/api/v1/status_by_cid/{consignment_id}",
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    async def track_by_invoice(self, invoice: str) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{settings.steadfast_base_url}/api/v1/status_by_invoice/{invoice}",
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    async def get_balance(self) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{settings.steadfast_base_url}/api/v1/get_balance",
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()
