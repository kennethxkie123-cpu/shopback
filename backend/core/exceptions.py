from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import Any, List, Optional
from backend.core.logging import logger

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[Any]] = None

async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP {exc.status_code} Error on {request.method} {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse(
            success=False,
            message=str(exc.detail),
            errors=[str(exc.detail)]
        ).model_dump()
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation Error on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=APIResponse(
            success=False,
            message="Request validation failed",
            errors=exc.errors()
        ).model_dump()
    )

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=APIResponse(
            success=False,
            message="An unexpected internal server error occurred.",
            errors=[str(exc)]
        ).model_dump()
    )
