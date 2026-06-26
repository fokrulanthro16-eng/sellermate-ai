"""Media upload — product images via S3/R2.

Falls back to base64 data URL preview when S3 is not configured.
"""
from __future__ import annotations

import io
import uuid
from typing import Optional

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.dependencies import CurrentMerchant

router = APIRouter()
settings = get_settings()

_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_MAX_SIZE = 5 * 1024 * 1024  # 5 MB


def _is_s3_configured() -> bool:
    return bool(settings.s3_bucket_name and settings.s3_access_key and settings.s3_secret_key)


async def _upload_s3(file_bytes: bytes, key: str, content_type: str) -> str:
    import boto3
    from botocore.config import Config
    s3 = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url or None,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region or "us-east-1",
        config=Config(signature_version="s3v4"),
    )
    s3.upload_fileobj(
        io.BytesIO(file_bytes),
        settings.s3_bucket_name,
        key,
        ExtraArgs={"ContentType": content_type, "ACL": "public-read"},
    )
    base = settings.s3_public_url or f"https://{settings.s3_bucket_name}.s3.amazonaws.com"
    return f"{base.rstrip('/')}/{key}"


@router.post("/upload")
async def upload_image(
    merchant: CurrentMerchant,
    file: UploadFile = File(...),
) -> dict:
    if file.content_type not in _ALLOWED_TYPES:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": {"code": "INVALID_FILE_TYPE",
                     "message": f"Allowed types: {', '.join(_ALLOWED_TYPES)}"}},
        )

    file_bytes = await file.read()
    if len(file_bytes) > _MAX_SIZE:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": {"code": "FILE_TOO_LARGE",
                     "message": "Maximum file size is 5 MB"}},
        )

    ext = (file.filename or "image.jpg").rsplit(".", 1)[-1].lower()
    key = f"merchants/{merchant.id}/products/{uuid.uuid4().hex}.{ext}"

    if _is_s3_configured():
        url = await _upload_s3(file_bytes, key, file.content_type or "image/jpeg")
        return {"success": True, "data": {"url": url, "key": key, "mode": "s3"}}

    # No S3 configured — return a data URL so the UI still works
    import base64
    data_url = f"data:{file.content_type};base64,{base64.b64encode(file_bytes).decode()}"
    return {
        "success": True,
        "data": {
            "url": data_url,
            "key": key,
            "mode": "local_preview",
            "note": "Configure S3/R2 credentials to persist images",
        },
    }


@router.post("/upload/logo")
async def upload_logo(
    merchant: CurrentMerchant,
    file: UploadFile = File(...),
) -> dict:
    """Upload merchant logo — same flow, different key path."""
    if file.content_type not in _ALLOWED_TYPES:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": {"code": "INVALID_FILE_TYPE",
                     "message": f"Allowed types: {', '.join(_ALLOWED_TYPES)}"}},
        )
    file_bytes = await file.read()
    if len(file_bytes) > _MAX_SIZE:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": {"code": "FILE_TOO_LARGE",
                     "message": "Maximum file size is 5 MB"}},
        )
    ext = (file.filename or "logo.jpg").rsplit(".", 1)[-1].lower()
    key = f"merchants/{merchant.id}/logo/{uuid.uuid4().hex}.{ext}"

    if _is_s3_configured():
        url = await _upload_s3(file_bytes, key, file.content_type or "image/jpeg")
        return {"success": True, "data": {"url": url, "key": key, "mode": "s3"}}

    import base64
    data_url = f"data:{file.content_type};base64,{base64.b64encode(file_bytes).decode()}"
    return {
        "success": True,
        "data": {"url": data_url, "key": key, "mode": "local_preview",
                 "note": "Configure S3/R2 credentials to persist images"},
    }
