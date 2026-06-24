import asyncio
import asyncpg


async def check():
    conn = await asyncpg.connect("postgresql://sellermate:password@localhost:5432/sellermate")
    tables = await conn.fetch(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )
    await conn.close()
    if tables:
        for t in tables:
            print(t["table_name"])
    else:
        print("NO TABLES FOUND")


asyncio.run(check())
