import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from influxdb_client import Point
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

from app.core.config import settings
from app.repositories.base import SensorRepository
from app.schemas.sensor_data import BatchIngestRequest

logger = structlog.get_logger(__name__)


class InfluxSensorRepository(SensorRepository):
    def __init__(self, client: InfluxDBClientAsync):
        self.client = client

    async def write_batch(self, batch: BatchIngestRequest) -> bool:
        write_api = self.client.write_api()
        points = []
        for payload in batch.payloads:
            point = (
                Point("sensor_data")
                .tag("machine_id", str(payload.machine_id))
                .time(payload.timestamp)
            )

            if payload.metrics.temperature is not None:
                point.field("temperature", payload.metrics.temperature)
            if payload.metrics.pressure is not None:
                point.field("pressure", payload.metrics.pressure)
            if payload.metrics.speed is not None:
                point.field("speed", payload.metrics.speed)

            points.append(point)

        try:
            await write_api.write(
                bucket=settings.TSDB_BUCKET,
                org=settings.TSDB_ORG,
                record=points,
            )
            logger.info(
                "Successfully queued points to InfluxDB",
                count=len(points),
                request_id=batch.request_id,
            )
            return True
        except Exception as e:
            logger.error(
                "Error writing to InfluxDB",
                error=str(e),
                request_id=batch.request_id,
            )
            raise e

    async def get_historical_data(
        self,
        machine_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
        interval: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query_api = self.client.query_api()

        flux_query = f'''
        from(bucket: "{settings.TSDB_BUCKET}")
          |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
          |> filter(fn: (r) => r["_measurement"] == "sensor_data")
          |> filter(fn: (r) => r["machine_id"] == "{str(machine_id)}")
        '''

        if interval:
            flux_query += f"""
              |> aggregateWindow(every: {interval}, fn: mean, createEmpty: false)
              |> yield(name: "mean")
            """

        try:
            result = await query_api.query(query=flux_query, org=settings.TSDB_ORG)

            parsed_data = []
            for table in result:
                for record in table.records:
                    parsed_data.append(
                        {
                            "time": record.get_time(),
                            "field": record.get_field(),
                            "value": record.get_value(),
                        }
                    )

            return parsed_data
        except Exception as e:
            logger.error(f"Failed to query InfluxDB: {str(e)}")
            raise e
