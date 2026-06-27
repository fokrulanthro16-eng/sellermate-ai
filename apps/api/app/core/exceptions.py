from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictException(HTTPException):
    def __init__(self, detail: str = "Resource already exists") -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Not authenticated") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Permission denied") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class BadRequestException(HTTPException):
    def __init__(self, detail: str = "Bad request") -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnprocessableException(HTTPException):
    def __init__(self, detail: str = "Unprocessable entity") -> None:
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class OutOfStockException(HTTPException):
    def __init__(self, detail: str = "One or more items are out of stock") -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class RateLimitException(HTTPException):
    def __init__(self, detail: str = "Too many requests", retry_after: int = 60) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(retry_after)},
        )


def _error_response(exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"code": exc.status_code, "message": exc.detail}},
        headers=getattr(exc, "headers", None) or {},
    )


async def not_found_handler(request: Request, exc: NotFoundException) -> JSONResponse:
    return _error_response(exc)


async def conflict_handler(request: Request, exc: ConflictException) -> JSONResponse:
    return _error_response(exc)


async def unauthorized_handler(request: Request, exc: UnauthorizedException) -> JSONResponse:
    return _error_response(exc)


async def forbidden_handler(request: Request, exc: ForbiddenException) -> JSONResponse:
    return _error_response(exc)


async def bad_request_handler(request: Request, exc: BadRequestException) -> JSONResponse:
    return _error_response(exc)


async def unprocessable_handler(request: Request, exc: UnprocessableException) -> JSONResponse:
    return _error_response(exc)


async def out_of_stock_handler(request: Request, exc: OutOfStockException) -> JSONResponse:
    return _error_response(exc)


async def rate_limit_handler(request: Request, exc: RateLimitException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"code": 429, "message": exc.detail}},
        headers=exc.headers or {},
    )
