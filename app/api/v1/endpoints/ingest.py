from fastapi import APIRouter, HTTPException, status
from app.schemas.sensor_data import BatchIngestRequest
from app.services.ingest import process_sensor_data_batch

router = APIRouter()

@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_sensor_data(request_body: BatchIngestRequest):
    """
    Ingest a batch of sensor data from an industrial gateway.
    
    - Validates gateway_id and limits batch payload size.
    - Ensures each payload has a valid UUID format for machine_id.
    - Validates that measurements fall within acceptable thresholds.
    - Validates timestamps.
    """
    # Push batch processing to the service layer
    try:
        await process_sensor_data_batch(batch=request_body)
        return {"status": "success", "message": f"Successfully queued {len(request_body.payloads)} data points for processing."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process ingestion batch"
        )
