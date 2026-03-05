from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from app.core.config import settings

def get_influx_client() -> InfluxDBClientAsync:
    """Dependency for getting InfluxDB async client"""
    return InfluxDBClientAsync(
        url=settings.INFLUXDB_URL,
        token=settings.INFLUXDB_TOKEN,
        org=settings.INFLUXDB_ORG
    )
