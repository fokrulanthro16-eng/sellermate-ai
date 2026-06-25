"""Backup router — export merchant data as JSON."""
from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import Response
from sqlalchemy import text

from app.core.dependencies import CurrentMerchant, DB
from app.services.audit_service import log_action

router = APIRouter(tags=["backup"])


@router.get("/export")
async def export_data(merchant: CurrentMerchant, db: DB) -> Response:
    m = merchant

    products_r = await db.execute(
        text("SELECT id, name, sku, category, base_price, sale_price, description, is_active, created_at FROM products WHERE merchant_id = :mid"),
        {"mid": m.id},
    )
    products = [dict(r._mapping) for r in products_r.fetchall()]

    customers_r = await db.execute(
        text("SELECT id, name, phone, email, district, source, total_orders, total_spent, created_at FROM customers WHERE merchant_id = :mid"),
        {"mid": m.id},
    )
    customers = [dict(r._mapping) for r in customers_r.fetchall()]

    orders_r = await db.execute(
        text("SELECT id, order_number, status, payment_status, total_amount, payment_method, "
             "delivery_address, delivery_district, courier_name, tracking_number, created_at "
             "FROM orders WHERE merchant_id = :mid ORDER BY created_at DESC LIMIT 1000"),
        {"mid": m.id},
    )
    orders = [dict(r._mapping) for r in orders_r.fetchall()]

    campaigns_r = await db.execute(
        text("SELECT id, title, campaign_type, status, language, provider, created_at FROM campaigns WHERE merchant_id = :mid"),
        {"mid": m.id},
    )
    campaigns = [dict(r._mapping) for r in campaigns_r.fetchall()]

    payload = {
        "export_version": "1.0",
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "merchant": {
            "id": m.id,
            "business_name": m.business_name,
            "owner_name": m.owner_name,
            "email": m.email,
            "phone": m.phone,
            "business_type": m.business_type.value if m.business_type else None,
            "district": m.district,
            "plan": m.plan.value if m.plan else None,
            "role": m.role.value if m.role else "OWNER",
        },
        "summary": {
            "products": len(products),
            "customers": len(customers),
            "orders": len(orders),
            "campaigns": len(campaigns),
        },
        "products": products,
        "customers": customers,
        "orders": orders,
        "campaigns": campaigns,
    }

    def _serial(obj):
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return str(obj)

    json_bytes = json.dumps(payload, ensure_ascii=False, indent=2, default=_serial).encode("utf-8")

    await log_action(db, m.id, "export", "backup", resource_label="full_export",
                     details={"products": len(products), "customers": len(customers), "orders": len(orders)})
    await db.commit()

    filename = f"sellermate_backup_{m.id[:8]}_{datetime.utcnow().strftime('%Y%m%d')}.json"
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/summary")
async def export_summary(merchant: CurrentMerchant, db: DB) -> dict:
    counts = {}
    for table in ("products", "customers", "orders", "campaigns"):
        r = await db.execute(text(f"SELECT COUNT(*) FROM {table} WHERE merchant_id = :mid"), {"mid": merchant.id})
        counts[table] = r.scalar() or 0
    return {"success": True, "data": {"counts": counts, "merchant_id": merchant.id}}
