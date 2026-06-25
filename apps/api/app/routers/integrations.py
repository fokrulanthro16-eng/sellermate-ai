"""
Integrations router — courier, payment, marketplace, notifications, documents.
All providers are mock until real credentials are configured in settings.
"""
from __future__ import annotations

import io
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select

from app.core.dependencies import CurrentMerchant, DB
from app.integrations.courier import courier_status_list, get_courier
from app.integrations.documents import generate_invoice, generate_shipping_label
from app.integrations.marketplace import get_marketplace, marketplace_status_list
from app.integrations.notification import NOTIFICATION_TYPES, get_notification_provider, notification_status_list
from app.integrations.payment import get_payment, payment_status_list
from app.models.integration_setting import IntegrationSettings

router = APIRouter(tags=["integrations"])

_DEFAULT_CONFIG: dict = {
    "courier":      {"active_provider": "manual", "pathao": {}, "steadfast": {}, "redx": {}},
    "payment":      {"active_provider": "cod",    "sslcommerz": {}, "bkash": {}, "nagad": {}},
    "marketplace":  {"facebook": {}, "daraz": {}, "shopify": {}},
    "notification": {"email": {}, "sms": {}, "whatsapp": {}},
}


# ── helpers ───────────────────────────────────────────────────────────────────

async def _get_or_create_settings(db, merchant_id: str) -> IntegrationSettings:
    result = await db.execute(select(IntegrationSettings).where(IntegrationSettings.merchant_id == merchant_id))
    row = result.scalar_one_or_none()
    if row is None:
        import copy
        row = IntegrationSettings(merchant_id=merchant_id, config_json=copy.deepcopy(_DEFAULT_CONFIG))
        db.add(row)
        await db.flush()
    return row


# ── status (no auth) ──────────────────────────────────────────────────────────

@router.get("/status")
async def integrations_status() -> dict:
    return {
        "courier":      courier_status_list(),
        "payment":      payment_status_list(),
        "marketplace":  marketplace_status_list(),
        "notification": notification_status_list(),
    }


# ── settings ──────────────────────────────────────────────────────────────────

@router.get("/settings")
async def get_settings(merchant: CurrentMerchant, db: DB) -> dict:
    row = await _get_or_create_settings(db, merchant.id)
    await db.commit()
    return {"success": True, "data": row.config_json}


class SettingsSaveBody(BaseModel):
    config: dict[str, Any]


@router.put("/settings")
async def save_settings(body: SettingsSaveBody, merchant: CurrentMerchant, db: DB) -> dict:
    row = await _get_or_create_settings(db, merchant.id)
    import copy
    merged = copy.deepcopy(row.config_json or _DEFAULT_CONFIG)
    for domain, cfg in body.config.items():
        if domain in merged:
            merged[domain].update(cfg)
        else:
            merged[domain] = cfg
    row.config_json = merged
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(row, "config_json")
    await db.commit()
    return {"success": True, "data": row.config_json}


# ── test connection ───────────────────────────────────────────────────────────

@router.post("/test/{domain}/{provider}")
async def test_connection(domain: str, provider: str, merchant: CurrentMerchant) -> dict:
    if domain == "courier":
        p = get_courier(provider)
    elif domain == "payment":
        p = get_payment(provider)
    elif domain == "marketplace":
        p = get_marketplace(provider)
    elif domain == "notification":
        p = get_notification_provider(provider)
    else:
        return {"success": False, "message": f"Unknown domain: {domain}"}
    result = await p.test_connection()
    return result


# ── courier ───────────────────────────────────────────────────────────────────

class CreateShipmentBody(BaseModel):
    order_id: str
    courier_name: str = "manual"


@router.post("/courier/shipment")
async def create_shipment(body: CreateShipmentBody, merchant: CurrentMerchant, db: DB) -> dict:
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT id, order_number, delivery_address, delivery_district, delivery_division, "
             "total_amount, payment_method, customer_id FROM orders WHERE id = :oid AND merchant_id = :mid"),
        {"oid": body.order_id, "mid": merchant.id},
    )
    row = result.fetchone()
    if not row:
        return {"success": False, "message": "Order not found"}

    order_dict = {
        "id": row.id, "order_number": row.order_number,
        "delivery_address": row.delivery_address, "delivery_district": row.delivery_district,
        "total_amount": float(row.total_amount), "payment_method": row.payment_method,
    }
    provider = get_courier(body.courier_name)
    shipment = await provider.create_shipment(order_dict)

    # Update order tracking number + courier name
    await db.execute(
        text("UPDATE orders SET tracking_number = :tid, courier_name = :cn WHERE id = :oid"),
        {"tid": shipment.tracking_id, "cn": body.courier_name, "oid": body.order_id},
    )
    await db.commit()

    return {
        "success": True,
        "data": {
            "tracking_id": shipment.tracking_id,
            "courier": shipment.courier,
            "status": shipment.status,
            "delivery_charge": shipment.delivery_charge,
            "estimated_delivery": shipment.estimated_delivery,
            "consignment_id": shipment.consignment_id,
        },
    }


@router.get("/courier/tracking/{tracking_id}")
async def get_tracking(tracking_id: str, merchant: CurrentMerchant) -> dict:
    prefix = tracking_id.split("-")[0].lower() if "-" in tracking_id else "manual"
    provider_map = {"pth": "pathao", "stf": "steadfast", "rdx": "redx", "man": "manual"}
    provider_name = provider_map.get(prefix, "manual")
    provider = get_courier(provider_name)
    info = await provider.get_tracking(tracking_id)
    return {
        "success": True,
        "data": {
            "tracking_id": info.tracking_id,
            "courier": info.courier,
            "status": info.status,
            "current_location": info.current_location,
            "estimated_delivery": info.estimated_delivery,
            "is_delivered": info.is_delivered,
            "is_returned": info.is_returned,
            "events": info.events,
        },
    }


@router.get("/courier/charge")
async def get_delivery_charge(
    district: str = Query("Dhaka"), courier: str = Query("pathao"), merchant: CurrentMerchant = None
) -> dict:
    provider = get_courier(courier)
    charge = await provider.get_charge(district)
    return {"success": True, "data": {"district": district, "courier": courier, "charge": charge}}


# ── payment ───────────────────────────────────────────────────────────────────

class PaymentIntentBody(BaseModel):
    order_id: str
    amount: float
    provider: str = "cod"


@router.post("/payment/intent")
async def create_payment_intent(body: PaymentIntentBody, merchant: CurrentMerchant) -> dict:
    provider = get_payment(body.provider)
    intent = await provider.create_intent(body.order_id, body.amount)
    return {
        "success": True,
        "data": {
            "payment_id": intent.payment_id,
            "provider": intent.provider,
            "status": intent.status,
            "amount": intent.amount,
            "currency": intent.currency,
            "payment_url": intent.payment_url,
        },
    }


@router.get("/payment/{payment_id}/status")
async def get_payment_status(payment_id: str, merchant: CurrentMerchant) -> dict:
    prefix = payment_id.split("-")[0].lower() if "-" in payment_id else "cod"
    provider_map = {"ssl": "sslcommerz", "bks": "bkash", "ngd": "nagad", "cod": "cod"}
    provider_name = provider_map.get(prefix, "cod")
    provider = get_payment(provider_name)
    status = await provider.get_status(payment_id)
    return {
        "success": True,
        "data": {
            "payment_id": status.payment_id,
            "provider": status.provider,
            "status": status.status,
            "is_paid": status.is_paid,
            "is_refunded": status.is_refunded,
            "transaction_id": status.transaction_id,
        },
    }


class RefundBody(BaseModel):
    amount: float


@router.post("/payment/{payment_id}/refund")
async def refund_payment(payment_id: str, body: RefundBody, merchant: CurrentMerchant) -> dict:
    prefix = payment_id.split("-")[0].lower() if "-" in payment_id else "cod"
    provider_map = {"ssl": "sslcommerz", "bks": "bkash", "ngd": "nagad"}
    provider = get_payment(provider_map.get(prefix, "cod"))
    result = await provider.refund(payment_id, body.amount)
    return {"success": True, "data": result}


# ── marketplace ───────────────────────────────────────────────────────────────

class MarketplaceSyncBody(BaseModel):
    provider: str = "manual"
    sync_type: str = "products"  # products | orders | all


@router.post("/marketplace/sync")
async def marketplace_sync(body: MarketplaceSyncBody, merchant: CurrentMerchant, db: DB) -> dict:
    from sqlalchemy import text
    provider = get_marketplace(body.provider)

    results = []
    if body.sync_type in ("products", "all"):
        r = await db.execute(text("SELECT COUNT(*) FROM products WHERE merchant_id = :mid"), {"mid": merchant.id})
        count = r.scalar() or 0
        res = await provider.sync_products(merchant.id, int(count))
        results.append({"type": "products", "synced": res.products_synced, "status": res.status, "message": res.message})

    if body.sync_type in ("orders", "all"):
        res = await provider.sync_orders(merchant.id)
        results.append({"type": "orders", "synced": res.orders_synced, "status": res.status, "message": res.message})

    return {"success": True, "data": {"provider": body.provider, "results": results, "last_sync": __import__("datetime").datetime.utcnow().isoformat()}}


@router.get("/marketplace/sync/status")
async def marketplace_sync_status(merchant: CurrentMerchant) -> dict:
    statuses = []
    for name in ("facebook", "daraz", "shopify", "manual"):
        p = get_marketplace(name)
        statuses.append({
            "provider": name, "display_name": p.display_name,
            "is_configured": p.is_configured(), "mode": "real" if p.is_configured() else "mock",
            "last_sync": None, "status": "never_synced",
        })
    return {"success": True, "data": statuses}


# ── notifications ─────────────────────────────────────────────────────────────

class SendNotificationBody(BaseModel):
    channel: str = "inapp"
    notification_type: str = "pending_order"
    recipient: str
    extra_body: str = ""


@router.post("/notifications/send")
async def send_notification(body: SendNotificationBody, merchant: CurrentMerchant) -> dict:
    tpl = NOTIFICATION_TYPES.get(body.notification_type, {"subject_bn": "বিজ্ঞপ্তি", "subject_en": "Notification"})
    subject = tpl["subject_en"]
    text_body = body.extra_body or f"SellerMate {body.notification_type.replace('_', ' ')} notification"
    provider = get_notification_provider(body.channel)
    result = await provider.send(body.recipient, subject, text_body)
    return {
        "success": True,
        "data": {
            "channel": result.channel,
            "recipient": result.recipient,
            "status": result.status,
            "message_id": result.message_id,
            "is_mock": result.is_mock,
        },
    }


@router.get("/notifications/types")
async def notification_types(merchant: CurrentMerchant) -> dict:
    return {"success": True, "data": NOTIFICATION_TYPES}


# ── documents ─────────────────────────────────────────────────────────────────

@router.get("/documents/invoice/{order_id}")
async def download_invoice(order_id: str, merchant: CurrentMerchant, db: DB) -> StreamingResponse:
    from sqlalchemy import text
    r = await db.execute(
        text("SELECT o.id, o.order_number, o.status, o.delivery_address, o.delivery_district, "
             "o.total_amount, o.subtotal, o.shipping_cost, o.discount_amount, "
             "o.payment_method, o.payment_status, c.name as customer_name, m.business_name "
             "FROM orders o JOIN customers c ON c.id = o.customer_id "
             "JOIN merchants m ON m.id = o.merchant_id "
             "WHERE o.id = :oid AND o.merchant_id = :mid"),
        {"oid": order_id, "mid": merchant.id},
    )
    row = r.fetchone()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Order not found")

    items_r = await db.execute(
        text("SELECT product_name, quantity, unit_price, total_price FROM order_items WHERE order_id = :oid"),
        {"oid": order_id},
    )
    items = [{"product_name": i.product_name, "quantity": i.quantity,
               "unit_price": float(i.unit_price), "total_price": float(i.total_price)}
             for i in items_r.fetchall()]

    order_dict = {
        "order_number": row.order_number, "status": row.status,
        "delivery_address": row.delivery_address, "delivery_district": row.delivery_district,
        "total_amount": float(row.total_amount), "subtotal": float(row.subtotal),
        "shipping_cost": float(row.shipping_cost), "discount_amount": float(row.discount_amount),
        "payment_method": row.payment_method, "customer_name": row.customer_name,
    }
    pdf_bytes = generate_invoice(order_dict, items, row.business_name or "SellerMate Merchant")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="invoice_{row.order_number}.pdf"'},
    )


@router.get("/documents/shipping-label/{order_id}")
async def download_shipping_label(
    order_id: str, merchant: CurrentMerchant, db: DB,
    courier: str = Query("manual"),
) -> StreamingResponse:
    from sqlalchemy import text
    r = await db.execute(
        text("SELECT o.id, o.order_number, o.delivery_address, o.delivery_district, "
             "o.total_amount, o.payment_method, o.tracking_number, o.courier_name, "
             "c.name as customer_name, m.business_name "
             "FROM orders o JOIN customers c ON c.id = o.customer_id "
             "JOIN merchants m ON m.id = o.merchant_id "
             "WHERE o.id = :oid AND o.merchant_id = :mid"),
        {"oid": order_id, "mid": merchant.id},
    )
    row = r.fetchone()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Order not found")

    courier_name = courier or row.courier_name or "manual"
    tracking_id = row.tracking_number
    if not tracking_id:
        provider = get_courier(courier_name)
        shipment = await provider.create_shipment({
            "id": order_id, "delivery_district": row.delivery_district or "Dhaka",
        })
        tracking_id = shipment.tracking_id

    order_dict = {
        "order_number": row.order_number, "delivery_address": row.delivery_address,
        "delivery_district": row.delivery_district, "total_amount": float(row.total_amount),
        "payment_method": row.payment_method, "customer_name": row.customer_name,
    }
    pdf_bytes = generate_shipping_label(order_dict, tracking_id, courier_name, row.business_name or "SellerMate Merchant")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="label_{row.order_number}.pdf"'},
    )
