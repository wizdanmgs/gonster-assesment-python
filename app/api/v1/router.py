from fastapi import APIRouter
from app.api.v1.endpoints import ingest, retrieve, machines, auth, config

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(ingest.router, prefix="/data", tags=["Data Ingestion"])
api_router.include_router(retrieve.router, prefix="/data", tags=["Data Retrieval"])
api_router.include_router(
    machines.router, prefix="/machines", tags=["Machine Management"]
)
api_router.include_router(
    config.router, prefix="/config", tags=["System Configuration"]
)
