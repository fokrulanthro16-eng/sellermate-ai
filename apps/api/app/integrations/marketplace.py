"""Marketplace sync providers — Facebook Shop, Daraz, Shopify, Manual."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SyncResult:
    provider: str
    products_synced: int
    orders_synced: int
    status: str  # success | failed | pending
    last_sync: str
    message: str


class MarketplaceProvider(ABC):
    name: str
    display_name: str

    def is_configured(self) -> bool:
        return False

    @abstractmethod
    async def sync_products(self, merchant_id: str, product_count: int) -> SyncResult: ...

    @abstractmethod
    async def sync_orders(self, merchant_id: str) -> SyncResult: ...

    async def get_sync_status(self, merchant_id: str) -> dict:
        return {
            "provider": self.name, "last_sync": datetime.utcnow().isoformat(),
            "status": "never_synced", "products_synced": 0, "orders_synced": 0,
        }

    async def test_connection(self) -> dict:
        return {"success": True, "mode": "mock", "message": "Mock connection OK"}


class FacebookShopProvider(MarketplaceProvider):
    name = "facebook"
    display_name = "Facebook Shop"

    def __init__(self, page_id: str = "", access_token: str = "") -> None:
        self._ok = bool(page_id and access_token)

    def is_configured(self) -> bool:
        return self._ok

    async def sync_products(self, merchant_id: str, product_count: int) -> SyncResult:
        return SyncResult(provider="facebook", products_synced=product_count, orders_synced=0,
                          status="success", last_sync=datetime.utcnow().isoformat(),
                          message=f"Mock: {product_count} পণ্য Facebook Shop-এ সিঙ্ক হয়েছে")

    async def sync_orders(self, merchant_id: str) -> SyncResult:
        return SyncResult(provider="facebook", products_synced=0, orders_synced=3,
                          status="success", last_sync=datetime.utcnow().isoformat(),
                          message="Mock: 3টি অর্ডার আমদানি হয়েছে")


class DarazProvider(MarketplaceProvider):
    name = "daraz"
    display_name = "Daraz"

    def __init__(self, app_key: str = "", signature: str = "") -> None:
        self._ok = bool(app_key and signature)

    def is_configured(self) -> bool:
        return self._ok

    async def sync_products(self, merchant_id: str, product_count: int) -> SyncResult:
        return SyncResult(provider="daraz", products_synced=product_count, orders_synced=0,
                          status="success", last_sync=datetime.utcnow().isoformat(),
                          message=f"Mock: {product_count} products synced to Daraz")

    async def sync_orders(self, merchant_id: str) -> SyncResult:
        return SyncResult(provider="daraz", products_synced=0, orders_synced=5,
                          status="success", last_sync=datetime.utcnow().isoformat(),
                          message="Mock: 5 orders imported from Daraz")


class ShopifyProvider(MarketplaceProvider):
    name = "shopify"
    display_name = "Shopify"

    def __init__(self, shop_url: str = "", access_token: str = "") -> None:
        self._ok = bool(shop_url and access_token)

    def is_configured(self) -> bool:
        return self._ok

    async def sync_products(self, merchant_id: str, product_count: int) -> SyncResult:
        return SyncResult(provider="shopify", products_synced=product_count, orders_synced=0,
                          status="success", last_sync=datetime.utcnow().isoformat(),
                          message=f"Mock: {product_count} products synced to Shopify")

    async def sync_orders(self, merchant_id: str) -> SyncResult:
        return SyncResult(provider="shopify", products_synced=0, orders_synced=2,
                          status="success", last_sync=datetime.utcnow().isoformat(),
                          message="Mock: 2 orders imported from Shopify")


class ManualImportProvider(MarketplaceProvider):
    name = "manual"
    display_name = "Manual Import"

    def is_configured(self) -> bool:
        return True

    async def sync_products(self, merchant_id: str, product_count: int) -> SyncResult:
        return SyncResult(provider="manual", products_synced=product_count, orders_synced=0,
                          status="success", last_sync=datetime.utcnow().isoformat(),
                          message=f"{product_count} products ready for manual export")

    async def sync_orders(self, merchant_id: str) -> SyncResult:
        return SyncResult(provider="manual", products_synced=0, orders_synced=0,
                          status="success", last_sync=datetime.utcnow().isoformat(),
                          message="Use CSV export to import orders manually")


_REGISTRY: dict[str, MarketplaceProvider] = {
    "facebook": FacebookShopProvider(),
    "daraz":    DarazProvider(),
    "shopify":  ShopifyProvider(),
    "manual":   ManualImportProvider(),
}


def get_marketplace(name: str) -> MarketplaceProvider:
    return _REGISTRY.get(name, _REGISTRY["manual"])


def marketplace_status_list() -> list[dict]:
    return [
        {
            "name": p.name, "display_name": p.display_name,
            "is_configured": p.is_configured(), "mode": "real" if p.is_configured() else "mock",
        }
        for p in _REGISTRY.values()
    ]
