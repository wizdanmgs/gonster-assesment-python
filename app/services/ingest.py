from typing import List
import logging
from app.schemas.sensor_data import BatchIngestRequest
from app.db.influx import get_influx_client
from influxdb_client import Point
from app.core.config import settings

logger = logging.getLogger(__name__)

async def process_sensor_data_batch(batch: BatchIngestRequest):
    """
    Process a batch of sensor data and store it into InfluxDB.
    """
    async with get_influx_client() as client:
        write_api = client.write_api()
        
        points = []
        for payload in batch.payloads:
            # Create a data point for InfluxDB measurement 'sensor_data'
            point = Point("sensor_data") \
                .tag("machine_id", str(payload.machine_id)) \
                .time(payload.timestamp)
            
            # Add fields dynamically based on available metrics
            if payload.metrics.temperature is not None:
                point.field("temperature", payload.metrics.temperature)
            if payload.metrics.pressure is not None:
                point.field("pressure", payload.metrics.pressure)
            if payload.metrics.speed is not None:
                point.field("speed", payload.metrics.speed)
                
            points.append(point)
            
        try:
            # Asynchronously write the data points to InfluxDB bucket
            await write_api.write(bucket=settings.INFLUXDB_BUCKET, org=settings.INFLUXDB_ORG, record=points)
            logger.info(f"Successfully queued {len(points)} points to InfluxDB")
            return True
        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {str(e)}")
            raise e
