from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(merchant_id: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": merchant_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.app_secret_key, algorithm=settings.app_algorithm)


def create_refresh_token(merchant_id: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": merchant_id,
        "iat": now,
        "exp": now + timedelta(days=settings.refresh_token_expire_days),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.app_secret_key, algorithm=settings.app_algorithm)


def decode_token(token: str) -> dict:
    """Raises jwt.PyJWTError on invalid/expired tokens."""
    return jwt.decode(token, settings.app_secret_key, algorithms=[settings.app_algorithm])
