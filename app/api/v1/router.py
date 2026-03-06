from fastapi import APIRouter, Depends

from app.api.deps import RoleChecker
from app.api.v1.endpoints import auth, config, ingest, machines, retrieve
from app.enums.role import UserRole

allow_svr = RoleChecker([UserRole.SUPERVISOR])
allow_opr = RoleChecker([UserRole.OPERATOR])
allow_mgr = RoleChecker([UserRole.MANAGEMENT])

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(
    ingest.router,
    prefix="/data",
    tags=["Data Ingestion"],
    dependencies=[Depends(allow_opr)],
)
api_router.include_router(
    retrieve.router,
    prefix="/data",
    tags=["Data Retrieval"],
    dependencies=[Depends(allow_opr)],
)
api_router.include_router(
    machines.router,
    prefix="/machines",
    tags=["Machine Management"],
    dependencies=[Depends(allow_svr)],
)
api_router.include_router(
    config.router,
    prefix="/config",
    tags=["System Configuration"],
    dependencies=[Depends(allow_mgr)],
)
