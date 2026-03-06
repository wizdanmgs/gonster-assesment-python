from datetime import datetime, timezone
from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.messages import MSG_ERROR, MSG_SUCCESS, get_message


def resp_success(
    data: Any = None, message: str = MSG_SUCCESS, status_code: int = 200
) -> JSONResponse:
    """
    Standardized success response helper.
    """
    content = {
        "success": True,
        "message": get_message(message),
        "data": data,
        "error": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return JSONResponse(status_code=status_code, content=jsonable_encoder(content))


def resp_error(
    message: str = MSG_ERROR,
    code: str = "INTERNAL_SERVER_ERROR",
    details: Any = None,
    status_code: int = 500,
) -> JSONResponse:
    """
    Standardized error response helper.
    """
    content = {
        "success": False,
        "message": get_message(message),
        "data": None,
        "error": {"code": code, "details": details},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return JSONResponse(status_code=status_code, content=jsonable_encoder(content))
