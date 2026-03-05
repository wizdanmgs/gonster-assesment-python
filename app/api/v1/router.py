from fastapi import APIRouter
from app.api.v1.endpoints import ingest, retrieve

api_router = APIRouter()
api_router.include_router(ingest.router, prefix="/data", tags=["Data Ingestion"])
api_router.include_router(retrieve.router, prefix="/data", tags=["Data Retrieval"])
