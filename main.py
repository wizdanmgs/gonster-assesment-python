import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.api.v1.router import api_router
from app.core.cache import close_cache, init_cache
from app.core.config import settings
from app.core.exceptions import (
    base_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.logger import setup_logging
from app.db.influx import get_influx_client
from app.db.migrations_util import run_migrations
from app.db.postgres import AsyncSessionLocal
from app.mqtt.broker import MQTTSubscriberService
from app.repositories.influx_sensor import InfluxSensorRepository
from app.repositories.sqlalchemy_machine import SqlAlchemyMachineRepository

logger = logging.getLogger(__name__)

# Setup structured logging
setup_logging()

# Run DB migrations synchronously before app init
run_migrations()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    On startup  → launch the MQTT subscriber as a background asyncio Task.
    On shutdown → signal the subscriber to stop and await its clean exit.
    """
    # Initialize Cache connection
    await init_cache()

    # Build repositories from existing DB helper generators
    async with AsyncSessionLocal() as session:
        machine_repo = SqlAlchemyMachineRepository(session)

        # InfluxDB uses an async generator context manager
        influx_gen = get_influx_client()
        influx_client = await influx_gen.__anext__()
        sensor_repo = InfluxSensorRepository(influx_client)

        mqtt_service = MQTTSubscriberService(
            sensor_repo=sensor_repo,
            machine_repo=machine_repo,
        )
        mqtt_task = asyncio.create_task(mqtt_service.start())
        logger.info(
            "MQTT subscriber task started (broker: %s:%d, topic: %s)",
            settings.MQTT_BROKER_HOST,
            settings.MQTT_BROKER_PORT,
            settings.MQTT_TOPIC_FILTER,
        )

        try:
            yield
        finally:
            logger.info("Shutting down MQTT subscriber…")
            await mqtt_service.stop()
            mqtt_task.cancel()
            try:
                await mqtt_task
            except asyncio.CancelledError:
                logger.info("MQTT subscriber task cancelled.")
            await influx_client.close()
            # Close the InfluxDB generator cleanly
            try:
                await influx_gen.__anext__()
            except StopAsyncIteration:
                pass

            # Close Redis cache
            await close_cache()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.PROJECT_VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    # Custom exception handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, base_exception_handler)

    # API router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host=settings.SERVER_HOST, port=settings.SERVER_PORT, reload=True
    )
