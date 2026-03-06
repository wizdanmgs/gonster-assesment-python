from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.sensor_data import BatchIngestRequest
from app.services.ingest import process_sensor_data_batch
from app.services import machine as machine_service
from app.api.deps import get_machine_repository, get_sensor_repository
from app.repositories.base import MachineRepository, SensorRepository
from app.core.responses import resp_success

router = APIRouter()

@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_sensor_data(
    request_body: BatchIngestRequest,
    machine_repo: MachineRepository = Depends(get_machine_repository),
    sensor_repo: SensorRepository = Depends(get_sensor_repository)
):
    """
    Ingest a batch of sensor data from an industrial gateway.
    
    - Validates that machine_ids exist in PostgreSQL.
    - Validates gateway_id and limits batch payload size.
    - Ensures each payload has a valid UUID format for machine_id.
    - Validates that measurements fall within acceptable thresholds.
    - Validates timestamps.
    """
    # Validate that all machine_ids exist in PostgreSQL
    machine_ids = [payload.machine_id for payload in request_body.payloads]
    invalid_ids = await machine_service.validate_machines_exist(repo=machine_repo, machine_ids=machine_ids)
    
    if invalid_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Machine(s) not found in registry: {', '.join(str(i) for i in invalid_ids)}"
        )

    # Push batch processing to the service layer
    await process_sensor_data_batch(repo=sensor_repo, batch=request_body)
    return resp_success(
        message=f"Successfully queued {len(request_body.payloads)} data points for processing.",
        status_code=status.HTTP_202_ACCEPTED
    )
