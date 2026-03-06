from datetime import datetime, timezone
from typing import Any

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.messages import MSG_ERROR, MSG_SUCCESS, get_message
from app.enums.status import ErrorStatus


def resp_success(
    data: Any = None, message: str = MSG_SUCCESS, status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """
    Standardized success response helper.
    """
    content = {
        "success": True,
        "status_code": status_code,
        "message": get_message(message),
        "data": data,
        "error": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return JSONResponse(status_code=status_code, content=jsonable_encoder(content))


def resp_error(
    message: str = MSG_ERROR,
    details: Any = None,
    status: str = ErrorStatus.INTERNAL_SERVER_ERROR,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> JSONResponse:
    """
    Standardized error response helper.
    """
    content = {
        "success": False,
        "status_code": status_code,
        "message": get_message(message),
        "data": None,
        "error": {"code": status, "details": details},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return JSONResponse(status_code=status_code, content=jsonable_encoder(content))
