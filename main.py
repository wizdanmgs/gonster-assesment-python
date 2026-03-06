from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.core.exceptions import validation_exception_handler
from app.api.v1.router import api_router
from app.db.migrations_util import run_migrations

# Run migrations on startup before app initialization
run_migrations()

def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Microservice for receiving, storing, and serving real-time sensor data from industrial machines",
        version="0.1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # Include custom exception handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    # Make sure to run the app as 'main:app' for live reload
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
