from fastapi import APIRouter, HTTPException, Query, Path, status, Depends
from typing import Optional
from datetime import datetime
import uuid
from app.services.retrieve import get_historical_data
from app.api.deps import get_sensor_repository
from app.repositories.base import SensorRepository
from app.core.responses import resp_success

router = APIRouter()

@router.get("/machine/{machine_id}")
async def get_machine_data(
    machine_id: uuid.UUID = Path(..., description="UUID of the machine"),
    start_time: datetime = Query(..., description="ISO 8601 Datetime for start of window"),
    end_time: datetime = Query(..., description="ISO 8601 Datetime for end of window"),
    interval: Optional[str] = Query(None, description="Aggregation interval e.g., '1m', '1h', '1d'"),
    repo: SensorRepository = Depends(get_sensor_repository)
):
    """
    Retrieve historical sensor data for a specific machine.
    """
    if start_time >= end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="start_time must be strictly before end_time"
        )
    
    data = await get_historical_data(
        repo=repo,
        machine_id=machine_id,
        start_time=start_time,
        end_time=end_time,
        interval=interval
    )
    
    return resp_success(
        data={
            "machine_id": machine_id,
            "start_time": start_time,
            "end_time": end_time,
            "interval": interval or "raw",
            "data": data
        },
        message="Historical data retrieved successfully"
    )
