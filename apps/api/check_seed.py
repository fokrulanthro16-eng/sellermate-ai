import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect("postgresql://sellermate:sellermate123@localhost:5432/sellermate")
    mid = await conn.fetchval("SELECT id FROM merchants WHERE email = 'demo@sellermate.ai'")
    products = await conn.fetchval("SELECT COUNT(*) FROM products WHERE merchant_id = $1", mid)
    variants = await conn.fetchval("SELECT COUNT(*) FROM product_variants WHERE product_id IN (SELECT id FROM products WHERE merchant_id = $1)", mid)
    customers = await conn.fetchval("SELECT COUNT(*) FROM customers WHERE merchant_id = $1", mid)
    orders = await conn.fetchval("SELECT COUNT(*) FROM orders WHERE merchant_id = $1", mid)
    delivered = await conn.fetchval("SELECT COUNT(*) FROM orders WHERE merchant_id = $1 AND status = 'DELIVERED'", mid)
    cancelled = await conn.fetchval("SELECT COUNT(*) FROM orders WHERE merchant_id = $1 AND status = 'CANCELLED'", mid)
    inv_logs = await conn.fetchval("SELECT COUNT(*) FROM inventory_logs WHERE merchant_id = $1", mid)
    print(f"products: {products}  variants: {variants}")
    print(f"customers: {customers}")
    print(f"orders: {orders}  delivered: {delivered}  cancelled: {cancelled}")
    print(f"inv_logs: {inv_logs}")
    await conn.close()

asyncio.run(check())
