import structlog

from app.repositories.base import SensorRepository
from app.schemas.sensor_data import BatchIngestRequest

logger = structlog.get_logger(__name__)


async def process_sensor_data_batch(repo: SensorRepository, batch: BatchIngestRequest):
    """
    Process a batch of sensor data and store it into InfluxDB.
    """
    logger.info(
        "Processing sensor data batch",
        request_id=batch.request_id,
        gateway_id=batch.gateway_id,
        batch_size=len(batch.payloads),
    )
    return await repo.write_batch(batch)
