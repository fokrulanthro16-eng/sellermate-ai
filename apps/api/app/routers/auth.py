from typing import Annotated

from fastapi import APIRouter, Depends, Header

from app.core.dependencies import CurrentMerchant, DB, RedisClient
from app.core.rate_limit import rate_limiter
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MerchantOut,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenPair,
    VerifyOTPRequest,
)
from app.schemas.common import MessageResponse, SuccessResponse
from app.services import auth_service

router = APIRouter(tags=["auth"])


@router.post(
    "/register",
    response_model=SuccessResponse[AuthResponse],
    status_code=201,
    dependencies=[Depends(rate_limiter("register", max_calls=3, window_seconds=60))],
)
async def register(body: RegisterRequest, db: DB, redis: RedisClient):
    result = await auth_service.register(db, redis, body)
    return SuccessResponse(data=result)


@router.post(
    "/login",
    response_model=SuccessResponse[AuthResponse],
    dependencies=[Depends(rate_limiter("login", max_calls=5, window_seconds=60))],
)
async def login(body: LoginRequest, db: DB, redis: RedisClient):
    result = await auth_service.login(db, redis, body)
    return SuccessResponse(data=result)


@router.post("/refresh", response_model=SuccessResponse[TokenPair])
async def refresh(body: RefreshRequest, db: DB, redis: RedisClient):
    tokens = await auth_service.refresh_tokens(db, redis, body.refresh_token)
    return SuccessResponse(data=tokens)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    merchant: CurrentMerchant,
    redis: RedisClient,
    authorization: Annotated[str | None, Header()] = None,
    body: RefreshRequest | None = None,
):
    access_token = (authorization or "").removeprefix("Bearer ")
    await auth_service.logout(redis, access_token, body.refresh_token if body else None)
    return MessageResponse(message="Logged out successfully")


@router.post(
    "/forgot-password",
    response_model=SuccessResponse[dict],
    dependencies=[Depends(rate_limiter("forgot_password", max_calls=3, window_seconds=60))],
)
async def forgot_password(body: ForgotPasswordRequest, db: DB, redis: RedisClient):
    otp = await auth_service.send_otp(db, redis, body.phone)
    payload: dict = {"message": "OTP sent to your phone"}
    # Expose OTP only in non-production environments
    from app.core.config import get_settings
    if not get_settings().is_production:
        payload["otp"] = otp
    return SuccessResponse(data=payload)


@router.post(
    "/verify-otp",
    response_model=MessageResponse,
    dependencies=[Depends(rate_limiter("verify_otp", max_calls=5, window_seconds=60))],
)
async def verify_otp(body: VerifyOTPRequest, redis: RedisClient):
    valid = await auth_service.verify_otp(redis, body.phone, body.otp)
    if not valid:
        from app.core.exceptions import BadRequestException
        raise BadRequestException("Invalid or expired OTP")
    return MessageResponse(message="OTP verified successfully")


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    dependencies=[Depends(rate_limiter("reset_password", max_calls=3, window_seconds=60))],
)
async def reset_password(body: ResetPasswordRequest, db: DB, redis: RedisClient):
    await auth_service.reset_password(db, redis, body.phone, body.otp, body.new_password)
    return MessageResponse(message="Password reset successfully")


@router.get("/me", response_model=SuccessResponse[MerchantOut])
async def me(merchant: CurrentMerchant):
    return SuccessResponse(data=MerchantOut.model_validate(merchant))
