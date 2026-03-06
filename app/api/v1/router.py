from fastapi import APIRouter, Depends

from app.api.deps import RoleChecker
from app.api.v1.endpoints import auth, config, ingest, machines, retrieve
from app.models.user import UserRole

require_management = RoleChecker([UserRole.Management])

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(
    ingest.router,
    prefix="/data",
    tags=["Data Ingestion"],
    dependencies=[Depends(require_management)],
)
api_router.include_router(retrieve.router, prefix="/data", tags=["Data Retrieval"])
api_router.include_router(
    machines.router,
    prefix="/machines",
    tags=["Machine Management"],
    dependencies=[Depends(require_management)],
)
api_router.include_router(
    config.router,
    prefix="/config",
    tags=["System Configuration"],
    dependencies=[Depends(require_management)],
)
