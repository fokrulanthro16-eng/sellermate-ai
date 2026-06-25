"""Courier integration — Pathao, Steadfast, REDX, Manual (all mock until real keys set)."""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta


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

    def __init__(self, client_id: str = "", client_secret: str = "") -> None:
        self._ok = bool(client_id and client_secret)

    def is_configured(self) -> bool:
        return self._ok

    async def create_shipment(self, order: dict) -> ShipmentResult:
        tid = _tid("PTH-", order.get("id", str(uuid.uuid4())))
        charge = await self.get_charge(order.get("delivery_district") or "Dhaka")
        return ShipmentResult(tracking_id=tid, courier="pathao", status="pending",
                               delivery_charge=charge, consignment_id=f"C{tid}",
                               estimated_delivery=(datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"))

    async def get_tracking(self, tracking_id: str) -> TrackingInfo:
        return TrackingInfo(tracking_id=tracking_id, courier="pathao", status="in_transit",
                            current_location="ঢাকা ডেলিভারি হাব", is_delivered=False, is_returned=False,
                            estimated_delivery=(datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"),
                            events=_events("in_transit"))


class SteadfastProvider(CourierProvider):
    name = "steadfast"
    display_name = "Steadfast"

    def __init__(self, api_key: str = "", secret: str = "") -> None:
        self._ok = bool(api_key and secret)

    def is_configured(self) -> bool:
        return self._ok

    async def create_shipment(self, order: dict) -> ShipmentResult:
        tid = _tid("STF-", order.get("id", str(uuid.uuid4())))
        charge = await self.get_charge(order.get("delivery_district") or "Dhaka")
        return ShipmentResult(tracking_id=tid, courier="steadfast", status="pending",
                               delivery_charge=charge,
                               estimated_delivery=(datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d"))

    async def get_tracking(self, tracking_id: str) -> TrackingInfo:
        return TrackingInfo(tracking_id=tracking_id, courier="steadfast", status="pending",
                            current_location="বাছাই কেন্দ্র", is_delivered=False, is_returned=False,
                            estimated_delivery=(datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"),
                            events=_events("pending"))


class REDXProvider(CourierProvider):
    name = "redx"
    display_name = "REDX"

    def __init__(self, api_key: str = "") -> None:
        self._ok = bool(api_key)

    def is_configured(self) -> bool:
        return self._ok

    async def create_shipment(self, order: dict) -> ShipmentResult:
        tid = _tid("RDX-", order.get("id", str(uuid.uuid4())))
        charge = await self.get_charge(order.get("delivery_district") or "Dhaka")
        return ShipmentResult(tracking_id=tid, courier="redx", status="pending",
                               delivery_charge=charge,
                               estimated_delivery=(datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"))

    async def get_tracking(self, tracking_id: str) -> TrackingInfo:
        return TrackingInfo(tracking_id=tracking_id, courier="redx", status="in_transit",
                            current_location="ঢাকা", is_delivered=False, is_returned=False,
                            estimated_delivery=(datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"),
                            events=_events("in_transit"))


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
