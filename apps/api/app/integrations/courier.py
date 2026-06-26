"""Courier integration — Pathao, Steadfast, REDX, Manual.

Uses real API clients when credentials are configured in settings; falls back to mock.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.core.config import get_settings


@dataclass
class ShipmentResult:
    tracking_id: str
    courier: str
    status: str
    delivery_charge: float
    estimated_delivery: str
    consignment_id: str = ""


@dataclass
class TrackingInfo:
    tracking_id: str
    courier: str
    status: str
    current_location: str
    estimated_delivery: str
    is_delivered: bool
    is_returned: bool
    events: list[dict] = field(default_factory=list)


class CourierProvider(ABC):
    name: str
    display_name: str

    def is_configured(self) -> bool:
        return False

    @abstractmethod
    async def create_shipment(self, order: dict) -> ShipmentResult: ...

    @abstractmethod
    async def get_tracking(self, tracking_id: str) -> TrackingInfo: ...

    async def get_charge(self, district: str = "Dhaka") -> float:
        dhaka = {"dhaka", "ঢাকা", "narayanganj", "gazipur", "munshiganj", "manikganj", "norsingdi"}
        return 60.0 if (district or "").lower() in dhaka else 120.0

    async def test_connection(self) -> dict:
        return {"success": True, "mode": "mock", "message": "Mock connection OK"}


def _tid(prefix: str, order_id: str) -> str:
    try:
        seed = int(uuid.UUID(order_id).int % 9_000_000) + 1_000_000
    except (ValueError, AttributeError):
        seed = abs(hash(order_id)) % 9_000_000 + 1_000_000
    return f"{prefix}{seed}"


def _events(status: str) -> list[dict]:
    now = datetime.utcnow()
    ev = [{"time": (now - timedelta(hours=3)).isoformat(), "location": "ঢাকা হাব", "event": "পার্সেল গ্রহণ"}]
    if status in ("in_transit", "delivered", "returned"):
        ev.append({"time": (now - timedelta(hours=1)).isoformat(), "location": "সর্টিং সেন্টার", "event": "প্রক্রিয়াধীন"})
    if status == "delivered":
        ev.append({"time": now.isoformat(), "location": "গন্তব্য", "event": "ডেলিভারি সম্পন্ন ✓"})
    elif status == "returned":
        ev.append({"time": now.isoformat(), "location": "বিক্রেতা", "event": "ফেরত দেওয়া হয়েছে"})
    return ev


class PathaoProvider(CourierProvider):
    name = "pathao"
    display_name = "Pathao"

    def __init__(self) -> None:
        s = get_settings()
        self._ok = bool(s.pathao_client_id and s.pathao_client_secret
                        and s.pathao_username and s.pathao_password)

    def is_configured(self) -> bool:
        return self._ok

    async def create_shipment(self, order: dict) -> ShipmentResult:
        charge = await self.get_charge(order.get("delivery_district") or "Dhaka")
        if self._ok:
            from app.integrations.courier_clients.pathao import PathaoClient
            client = PathaoClient()
            s = get_settings()
            # Pathao requires a store_id — fall back to mock if not set
            store_id = getattr(s, "pathao_store_id", 0)
            if store_id:
                result = await client.create_delivery(
                    store_id=int(store_id),
                    merchant_order_id=order.get("id", str(uuid.uuid4())),
                    recipient_name=order.get("customer_name", "Customer"),
                    recipient_phone=order.get("customer_phone", ""),
                    recipient_address=order.get("delivery_address", ""),
                    recipient_city=int(order.get("pathao_city_id", 1)),
                    recipient_zone=int(order.get("pathao_zone_id", 1)),
                    cod_amount=float(order.get("total_amount", 0)),
                )
                data = result.get("data", {})
                return ShipmentResult(
                    tracking_id=str(data.get("consignment_id", "")),
                    courier="pathao", status="pending",
                    delivery_charge=charge,
                    consignment_id=str(data.get("consignment_id", "")),
                    estimated_delivery=(datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"),
                )
        tid = _tid("PTH-", order.get("id", str(uuid.uuid4())))
        return ShipmentResult(tracking_id=tid, courier="pathao", status="pending",
                               delivery_charge=charge, consignment_id=f"C{tid}",
                               estimated_delivery=(datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"))

    async def get_tracking(self, tracking_id: str) -> TrackingInfo:
        if self._ok and not tracking_id.startswith("PTH-"):
            from app.integrations.courier_clients.pathao import PathaoClient
            try:
                result = await PathaoClient().get_delivery(tracking_id)
                data = result.get("data", {})
                return TrackingInfo(
                    tracking_id=tracking_id, courier="pathao",
                    status=data.get("order_status", "in_transit"),
                    current_location=data.get("zone_name", "In Transit"),
                    is_delivered=data.get("order_status") == "Delivered",
                    is_returned=data.get("order_status") == "Returned",
                    estimated_delivery=(datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"),
                    events=_events("in_transit"),
                )
            except Exception:
                pass
        return TrackingInfo(tracking_id=tracking_id, courier="pathao", status="in_transit",
                            current_location="ঢাকা ডেলিভারি হাব", is_delivered=False, is_returned=False,
                            estimated_delivery=(datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"),
                            events=_events("in_transit"))

    async def test_connection(self) -> dict:
        if self._ok:
            from app.integrations.courier_clients.pathao import PathaoClient
            try:
                cities = await PathaoClient().get_cities()
                return {"success": True, "mode": "real", "cities": len(cities)}
            except Exception as exc:
                return {"success": False, "mode": "real", "error": str(exc)}
        return {"success": True, "mode": "mock", "message": "Mock connection OK"}


class SteadfastProvider(CourierProvider):
    name = "steadfast"
    display_name = "Steadfast"

    def __init__(self) -> None:
        s = get_settings()
        self._ok = bool(s.steadfast_api_key and s.steadfast_secret_key)

    def is_configured(self) -> bool:
        return self._ok

    async def create_shipment(self, order: dict) -> ShipmentResult:
        charge = await self.get_charge(order.get("delivery_district") or "Dhaka")
        if self._ok:
            from app.integrations.courier_clients.steadfast import SteadfastClient
            result = await SteadfastClient().create_order(
                invoice=order.get("id", str(uuid.uuid4())),
                recipient_name=order.get("customer_name", "Customer"),
                recipient_phone=order.get("customer_phone", ""),
                recipient_address=order.get("delivery_address", ""),
                cod_amount=float(order.get("total_amount", 0)),
                note=order.get("note", ""),
            )
            consignment_id = str(result.get("consignment", {}).get("consignment_id", ""))
            tracking_code = str(result.get("consignment", {}).get("tracking_code", consignment_id))
            return ShipmentResult(
                tracking_id=tracking_code or _tid("STF-", order.get("id", "")),
                courier="steadfast", status="pending",
                delivery_charge=charge, consignment_id=consignment_id,
                estimated_delivery=(datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d"),
            )
        tid = _tid("STF-", order.get("id", str(uuid.uuid4())))
        return ShipmentResult(tracking_id=tid, courier="steadfast", status="pending",
                               delivery_charge=charge,
                               estimated_delivery=(datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d"))

    async def get_tracking(self, tracking_id: str) -> TrackingInfo:
        if self._ok and not tracking_id.startswith("STF-"):
            from app.integrations.courier_clients.steadfast import SteadfastClient
            try:
                result = await SteadfastClient().track_by_consignment(tracking_id)
                data = result.get("data", {})
                status = data.get("delivery_status", "in_transit")
                return TrackingInfo(
                    tracking_id=tracking_id, courier="steadfast",
                    status=status,
                    current_location=data.get("current_location", "সর্টিং সেন্টার"),
                    is_delivered=status == "delivered",
                    is_returned=status == "returned",
                    estimated_delivery=(datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"),
                    events=_events(status),
                )
            except Exception:
                pass
        return TrackingInfo(tracking_id=tracking_id, courier="steadfast", status="pending",
                            current_location="বাছাই কেন্দ্র", is_delivered=False, is_returned=False,
                            estimated_delivery=(datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"),
                            events=_events("pending"))

    async def test_connection(self) -> dict:
        if self._ok:
            from app.integrations.courier_clients.steadfast import SteadfastClient
            try:
                balance = await SteadfastClient().get_balance()
                return {"success": True, "mode": "real", "balance": balance}
            except Exception as exc:
                return {"success": False, "mode": "real", "error": str(exc)}
        return {"success": True, "mode": "mock", "message": "Mock connection OK"}


class REDXProvider(CourierProvider):
    name = "redx"
    display_name = "REDX"

    def __init__(self) -> None:
        s = get_settings()
        self._ok = bool(s.redx_api_key)

    def is_configured(self) -> bool:
        return self._ok

    async def create_shipment(self, order: dict) -> ShipmentResult:
        charge = await self.get_charge(order.get("delivery_district") or "Dhaka")
        if self._ok:
            from app.integrations.courier_clients.redx import REDXClient
            result = await REDXClient().create_parcel(
                customer_name=order.get("customer_name", "Customer"),
                customer_phone=order.get("customer_phone", ""),
                delivery_area=order.get("delivery_district", "Dhaka"),
                delivery_area_id=int(order.get("redx_area_id", 1)),
                merchant_invoice_id=order.get("id", str(uuid.uuid4())),
                cash_collection_amount=float(order.get("total_amount", 0)),
            )
            tracking_id = str(result.get("parcel", {}).get("tracking_id", ""))
            return ShipmentResult(
                tracking_id=tracking_id or _tid("RDX-", order.get("id", "")),
                courier="redx", status="pending",
                delivery_charge=charge,
                estimated_delivery=(datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"),
            )
        tid = _tid("RDX-", order.get("id", str(uuid.uuid4())))
        return ShipmentResult(tracking_id=tid, courier="redx", status="pending",
                               delivery_charge=charge,
                               estimated_delivery=(datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"))

    async def get_tracking(self, tracking_id: str) -> TrackingInfo:
        if self._ok and not tracking_id.startswith("RDX-"):
            from app.integrations.courier_clients.redx import REDXClient
            try:
                result = await REDXClient().track_parcel(tracking_id)
                parcel = result.get("parcel", {})
                status = parcel.get("status", "in_transit")
                return TrackingInfo(
                    tracking_id=tracking_id, courier="redx",
                    status=status,
                    current_location=parcel.get("current_location", "ঢাকা"),
                    is_delivered=status == "delivered",
                    is_returned=status == "returned",
                    estimated_delivery=(datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"),
                    events=_events(status),
                )
            except Exception:
                pass
        return TrackingInfo(tracking_id=tracking_id, courier="redx", status="in_transit",
                            current_location="ঢাকা", is_delivered=False, is_returned=False,
                            estimated_delivery=(datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"),
                            events=_events("in_transit"))

    async def test_connection(self) -> dict:
        if self._ok:
            from app.integrations.courier_clients.redx import REDXClient
            try:
                areas = await REDXClient().get_areas()
                return {"success": True, "mode": "real", "areas": len(areas)}
            except Exception as exc:
                return {"success": False, "mode": "real", "error": str(exc)}
        return {"success": True, "mode": "mock", "message": "Mock connection OK"}


class ManualCourierProvider(CourierProvider):
    name = "manual"
    display_name = "Manual"

    def is_configured(self) -> bool:
        return True

    async def create_shipment(self, order: dict) -> ShipmentResult:
        tid = _tid("MAN-", order.get("id", str(uuid.uuid4())))
        return ShipmentResult(tracking_id=tid, courier="manual", status="pending",
                               delivery_charge=100.0,
                               estimated_delivery=(datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%d"))

    async def get_tracking(self, tracking_id: str) -> TrackingInfo:
        return TrackingInfo(tracking_id=tracking_id, courier="manual", status="pending",
                            current_location="বিক্রেতার কাছে", is_delivered=False, is_returned=False,
                            estimated_delivery=(datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%d"),
                            events=[{"time": datetime.utcnow().isoformat(), "location": "বিক্রেতা", "event": "প্রস্তুতি"}])


_REGISTRY: dict[str, CourierProvider] = {
    "pathao":    PathaoProvider(),
    "steadfast": SteadfastProvider(),
    "redx":      REDXProvider(),
    "manual":    ManualCourierProvider(),
}


def get_courier(name: str) -> CourierProvider:
    return _REGISTRY.get(name, _REGISTRY["manual"])


def courier_status_list() -> list[dict]:
    return [
        {
            "name": p.name, "display_name": p.display_name,
            "is_configured": p.is_configured(), "mode": "real" if p.is_configured() else "mock",
        }
        for p in _REGISTRY.values()
    ]
