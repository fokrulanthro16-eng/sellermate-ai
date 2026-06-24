import asyncio
import asyncpg


async def setup():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/postgres")

    # Restore the original password from .env
    try:
        await conn.execute("ALTER USER sellermate WITH PASSWORD 'sellermate123'")
        print("Restored sellermate password to 'sellermate123'")
    except Exception as e:
        print(f"Password update: {e}")

    # Grant schema ownership in test db
    conn2 = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/sellermate_test")
    try:
        await conn2.execute("GRANT ALL ON SCHEMA public TO sellermate")
        print("Schema privileges confirmed on sellermate_test")
    except Exception as e:
        print(f"Schema grant: {e}")
    await conn2.close()

    await conn.close()
    print("Done")


asyncio.run(setup())
