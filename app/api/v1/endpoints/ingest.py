from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.sensor_data import BatchIngestRequest
from app.services.ingest import process_sensor_data_batch
from app.services import machine as machine_service
from app.db.postgres import get_db

router = APIRouter()

@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_sensor_data(
    request_body: BatchIngestRequest,
    db: AsyncSession = Depends(get_db)
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
    invalid_ids = await machine_service.validate_machines_exist(db=db, machine_ids=machine_ids)
    
    if invalid_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Machine(s) not found in registry: {', '.join(str(i) for i in invalid_ids)}"
        )

    # Push batch processing to the service layer
    try:
        await process_sensor_data_batch(batch=request_body)
        return {"status": "success", "message": f"Successfully queued {len(request_body.payloads)} data points for processing."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process ingestion batch"
        )
