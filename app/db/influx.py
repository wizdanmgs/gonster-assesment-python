from typing import AsyncGenerator

from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

from app.core.config import settings


async def get_influx_client() -> AsyncGenerator[InfluxDBClientAsync, None]:
    """Dependency for getting InfluxDB async client"""
    async with InfluxDBClientAsync(
        url=settings.TSDB_URL,
        token=settings.TSDB_TOKEN,
        org=settings.TSDB_ORG,
    ) as client:
        yield client
