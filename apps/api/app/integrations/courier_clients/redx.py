"""REDX courier API client — https://openapi.redx.com.bd"""
from __future__ import annotations

import httpx
from app.core.config import get_settings

settings = get_settings()


class REDXClient:
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {settings.redx_api_key}",
            "Content-Type": "application/json",
        }

    async def create_parcel(
        self,
        customer_name: str,
        customer_phone: str,
        delivery_area: str,
        delivery_area_id: int,
        merchant_invoice_id: str,
        cash_collection_amount: float,
        parcel_weight: int = 500,  # grams
        instruction: str = "",
        value: float = 0,
    ) -> dict:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{settings.redx_base_url}/v1.0.0-beta/parcel",
                headers=self._headers(),
                json={
                    "customer_name": customer_name,
                    "customer_phone": customer_phone,
                    "delivery_area": delivery_area,
                    "delivery_area_id": delivery_area_id,
                    "merchant_invoice_id": merchant_invoice_id,
                    "cash_collection_amount": cash_collection_amount,
                    "parcel_weight": parcel_weight,
                    "instruction": instruction,
                    "value": value,
                },
            )
            r.raise_for_status()
            return r.json()

    async def track_parcel(self, tracking_id: str) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{settings.redx_base_url}/v1.0.0-beta/parcel/{tracking_id}/info",
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    async def get_areas(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{settings.redx_base_url}/v1.0.0-beta/areas",
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json().get("areas", [])
