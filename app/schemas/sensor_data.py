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
    def validate_timestamp(cls, v: datetime):
        now = datetime.now(timezone.utc)
        # Timestamp cannot be significantly in the future (more than 60 seconds)
        if v.timestamp() > now.timestamp() + 60:
            raise ValueError("Timestamp cannot be significantly in the future")

        # Timestamp cannot be too old (more than 7 days)
        if v.timestamp() < (now.timestamp() - 7 * 24 * 60 * 60):
            raise ValueError("Timestamp is too old (limit is 7 days)")

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
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Identifier of the gateway (alphanumeric, underscores, hyphens)",
    )
    payloads: List[SensorDataPayload] = Field(
        ..., min_length=1, max_length=1000, description="List of sensor data points"
    )
