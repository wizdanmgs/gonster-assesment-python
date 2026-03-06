from fastapi import Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from app.core.responses import resp_error
import logging

logger = logging.getLogger(__name__)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom exception handler for validation errors to return a clean, actionable response.
    """
    logger.error(f"Validation error: {exc.errors()}")
    return resp_error(
        message="Invalid input data format or values.",
        code="VALIDATION_ERROR",
        details=exc.errors(),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom exception handler for FastAPI HTTPException.
    """
    return resp_error(
        message=exc.detail,
        code="HTTP_EXCEPTION",
        status_code=exc.status_code
    )

async def base_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for all unhandled exceptions.
    """
    logger.exception(f"Unhandled exception: {str(exc)}")
    return resp_error(
        message="An unexpected error occurred.",
        code="INTERNAL_SERVER_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
