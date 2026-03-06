import logging

from app.repositories.base import SensorRepository
from app.schemas.sensor_data import BatchIngestRequest

logger = logging.getLogger(__name__)


async def process_sensor_data_batch(repo: SensorRepository, batch: BatchIngestRequest):
    """
    Process a batch of sensor data and store it into InfluxDB.
    """
    return await repo.write_batch(batch)
