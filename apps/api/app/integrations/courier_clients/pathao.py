"""Pathao courier API client — https://hermes.pathao.com"""
from __future__ import annotations

import time

import httpx
from app.core.config import get_settings

settings = get_settings()

_token_store: dict = {}


class PathaoClient:
    async def _get_token(self) -> str:
        now = time.time()
        if _token_store.get("expires_at", 0) > now:
            return _token_store["token"]

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"{settings.pathao_base_url}/aladdin/api/v1/issue-token",
                json={
                    "client_id": settings.pathao_client_id,
                    "client_secret": settings.pathao_client_secret,
                    "username": settings.pathao_username,
                    "password": settings.pathao_password,
                    "grant_type": "password",
                },
            )
            r.raise_for_status()
            data = r.json()

        token = data.get("access_token", "")
        _token_store["token"] = token
        _token_store["expires_at"] = now + data.get("expires_in", 3600) - 60
        return token

    async def create_delivery(
        self,
        store_id: int,
        merchant_order_id: str,
        recipient_name: str,
        recipient_phone: str,
        recipient_address: str,
        recipient_city: int,
        recipient_zone: int,
        cod_amount: float,
        item_quantity: int = 1,
        item_weight: float = 0.5,
        item_description: str = "",
        delivery_type: int = 48,
        item_type: int = 2,
        recipient_area: int | None = None,
    ) -> dict:
        token = await self._get_token()
        payload: dict = {
            "store_id": store_id,
            "merchant_order_id": merchant_order_id,
            "recipient_name": recipient_name,
            "recipient_phone": recipient_phone,
            "recipient_address": recipient_address,
            "recipient_city": recipient_city,
            "recipient_zone": recipient_zone,
            "delivery_type": delivery_type,
            "item_type": item_type,
            "item_quantity": item_quantity,
            "item_weight": item_weight,
            "amount_to_collect": cod_amount,
            "item_description": item_description,
        }
        if recipient_area:
            payload["recipient_area"] = recipient_area

        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{settings.pathao_base_url}/aladdin/api/v1/deliveries",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            )
            r.raise_for_status()
            return r.json()

    async def get_delivery(self, delivery_id: str) -> dict:
        token = await self._get_token()
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{settings.pathao_base_url}/aladdin/api/v1/deliveries/{delivery_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            r.raise_for_status()
            return r.json()

    async def get_cities(self) -> list[dict]:
        token = await self._get_token()
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{settings.pathao_base_url}/aladdin/api/v1/cities",
                headers={"Authorization": f"Bearer {token}"},
            )
            r.raise_for_status()
            return r.json().get("data", {}).get("cities", [])

    async def get_zones(self, city_id: int) -> list[dict]:
        token = await self._get_token()
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{settings.pathao_base_url}/aladdin/api/v1/cities/{city_id}/zone-list",
                headers={"Authorization": f"Bearer {token}"},
            )
            r.raise_for_status()
            return r.json().get("data", {}).get("zones", [])

    async def price_plan(self, store_id: int, item_type: int, delivery_type: int,
                         weight: float, recipient_city: int, recipient_zone: int) -> dict:
        token = await self._get_token()
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{settings.pathao_base_url}/aladdin/api/v1/merchant/price-plan",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "store_id": store_id,
                    "item_type": item_type,
                    "delivery_type": delivery_type,
                    "item_weight": weight,
                    "recipient_city": recipient_city,
                    "recipient_zone": recipient_zone,
                },
            )
            r.raise_for_status()
            return r.json()
