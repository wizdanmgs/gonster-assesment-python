from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.core.exceptions import (
    validation_exception_handler,
    http_exception_handler,
    base_exception_handler
)
from app.api.v1.router import api_router
from app.db.migrations_util import run_migrations

# Run migrations on startup before app initialization
run_migrations()

def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.PROJECT_VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # Include custom exception handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, base_exception_handler)

    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    # Make sure to run the app as 'main:app' for live reload
    uvicorn.run("main:app", host=settings.SERVER_HOST, port=settings.SERVER_PORT, reload=True)
