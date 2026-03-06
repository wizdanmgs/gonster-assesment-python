import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.repositories.base import SensorRepository


async def get_historical_data(
    repo: SensorRepository,
    machine_id: uuid.UUID,
    start_time: datetime,
    end_time: datetime,
    interval: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve historical data from InfluxDB using Flux query.
    """
    return await repo.get_historical_data(machine_id, start_time, end_time, interval)
