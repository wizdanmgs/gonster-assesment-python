import uuid
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class SensorMetrics(BaseModel):
    temperature: Optional[float] = Field(
        None, description="Current temperature in Celsius", ge=-50, le=500
    )
    pressure: Optional[float] = Field(
        None, description="Current pressure in Bar", ge=0, le=100
    )
    speed: Optional[float] = Field(
        None, description="Current speed in RPM", ge=0, le=20000
    )


class SensorDataPayload(BaseModel):
    machine_id: uuid.UUID = Field(
        ..., description="Unique identifier of the machine (UUID format)"
    )
    timestamp: datetime = Field(
        ..., description="Timestamp of the measurement (ISO 8601 format)"
    )
    metrics: SensorMetrics = Field(..., description="The sensor metrics measured")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_not_in_future(cls, v: datetime):
        if v.timestamp() > datetime.now(timezone.utc).timestamp() + 60:
            raise ValueError("Timestamp cannot be significantly in the future")
        return v

    @field_validator("metrics")
    @classmethod
    def check_at_least_one_metric(cls, v: SensorMetrics):
        if v.temperature is None and v.pressure is None and v.speed is None:
            raise ValueError("At least one sensor metric must be provided")
        return v


class BatchIngestRequest(BaseModel):
    request_id: Optional[str] = Field(
        None, description="Unique identifier for the request"
    )
    gateway_id: str = Field(
        ..., min_length=1, max_length=100, description="Identifier of the gateway"
    )
    payloads: List[SensorDataPayload] = Field(
        ..., min_length=1, max_length=1000, description="List of sensor data points"
    )
