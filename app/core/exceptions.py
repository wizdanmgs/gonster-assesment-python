import logging

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError

from app.core.messages import (
    MSG_INTERNAL_SERVER_ERROR,
    MSG_VALIDATION_ERROR,
)
from app.core.responses import resp_error
from app.enums.status import ErrorStatus

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom exception handler for validation errors to return a clean, actionable response.
    """
    logger.error(f"Validation error: {exc.errors()}")
    return resp_error(
        message=MSG_VALIDATION_ERROR,
        status="UNPROCESSABLE_CONTENT",
        details=exc.errors(),
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom exception handler for FastAPI HTTPException.
    """
    err_status = ErrorStatus.BAD_REQUEST
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        err_status = ErrorStatus.UNAUTHORIZED
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        err_status = ErrorStatus.FORBIDDEN
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        err_status = ErrorStatus.NOT_FOUND
    elif exc.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
        err_status = ErrorStatus.UNPROCESSABLE_CONTENT
    elif exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
        err_status = ErrorStatus.INTERNAL_SERVER_ERROR

    return resp_error(
        message=exc.detail, status=err_status, status_code=exc.status_code
    )


async def base_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for all unhandled exceptions.
    """
    logger.exception(f"Unhandled exception: {str(exc)}")
    return resp_error(
        message=MSG_INTERNAL_SERVER_ERROR,
        status="INTERNAL_SERVER_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
