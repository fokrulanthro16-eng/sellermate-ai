import pytest
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.session import get_db
from app.db.redis import get_redis
from app.main import app
from app.models.base import Base
from app import models as _models  # noqa: F401 — ensures all ORM classes are registered

TEST_DATABASE_URL = "postgresql+asyncpg://sellermate:sellermate123@localhost:5432/sellermate_test"
TEST_REDIS_URL = "redis://localhost:6379/1"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()


@pytest.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def redis_client():
    try:
        from redis.asyncio import from_url
        real: Redis = from_url(TEST_REDIS_URL, decode_responses=True)
        await real.ping()
        client: Redis = real
        use_real = True
    except Exception:
        import fakeredis.aioredis  # type: ignore[import-untyped]
        client = fakeredis.aioredis.FakeRedis(decode_responses=True)
        use_real = False

    yield client

    await client.flushdb()
    if use_real:
        await client.aclose()


@pytest.fixture
async def client(db_session: AsyncSession, redis_client: Redis):
    async def override_db():
        yield db_session

    async def override_redis():
        return redis_client

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def register_payload() -> dict:
    return {
        "email": "test@example.com",
        "phone": "+8801712345678",
        "password": "Test1234!",
        "business_name": "Test Shop",
        "owner_name": "Test Owner",
        "business_type": "FASHION_CLOTHING",
    }
