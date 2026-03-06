from datetime import datetime, timezone
from typing import Any, Optional, Union
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

def resp_success(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200
) -> JSONResponse:
    """
    Standardized success response helper.
    """
    content = {
        "success": True,
        "message": message,
        "data": data,
        "error": None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    return JSONResponse(status_code=status_code, content=jsonable_encoder(content))

def resp_error(
    message: str = "Error",
    code: str = "INTERNAL_SERVER_ERROR",
    details: Any = None,
    status_code: int = 500
) -> JSONResponse:
    """
    Standardized error response helper.
    """
    content = {
        "success": False,
        "message": message,
        "data": None,
        "error": {
            "code": code,
            "details": details
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    return JSONResponse(status_code=status_code, content=jsonable_encoder(content))
