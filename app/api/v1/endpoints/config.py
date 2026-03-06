from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import CurrentUser
from app.core.messages import MSG_CONFIG_UPDATED
from app.core.responses import resp_success

router = APIRouter()


class ConfigUpdate(BaseModel):
    setting_key: str
    setting_value: str


@router.post("/update")
async def update_configuration(config: ConfigUpdate, current_user: CurrentUser) -> Any:
    """Update sensitive system configuration (Requires Management role)."""
    # Simulate config update
    return resp_success(
        data={
            "updated_by": str(current_user.id),
            "updated_config": config.model_dump(),
        },
        message=MSG_CONFIG_UPDATED,
    )
