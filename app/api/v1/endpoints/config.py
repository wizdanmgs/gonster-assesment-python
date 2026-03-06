from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any

from app.api.deps import CurrentUser, RoleChecker
from app.models.user import UserRole
from app.core.responses import resp_success
from app.core.messages import MSG_CONFIG_UPDATED

router = APIRouter()

class ConfigUpdate(BaseModel):
    setting_key: str
    setting_value: str

# Only users with Management role can access this
require_management = RoleChecker([UserRole.Management])

@router.post("/update", dependencies=[Depends(require_management)])
async def update_configuration(
    config: ConfigUpdate,
    current_user: CurrentUser
) -> Any:
    """Update sensitive system configuration (Requires Management role)."""
    # Simulate config update
    return resp_success(
        data={
            "updated_by": str(current_user.id),
            "updated_config": config.model_dump()
        },
        message=MSG_CONFIG_UPDATED
    )
