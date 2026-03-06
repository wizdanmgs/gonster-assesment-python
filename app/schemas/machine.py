import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MachineBase(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the machine"
    )
    location: str = Field(
        ..., min_length=1, max_length=255, description="Location of the machine"
    )
    sensor_type: str = Field(
        ..., min_length=1, max_length=100, description="Type of sensors on the machine"
    )
    status: str = Field(
        "active", max_length=50, description="Current status of the machine"
    )


class MachineCreate(MachineBase):
    pass


class MachineUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    location: Optional[str] = Field(None, min_length=1, max_length=255)
    sensor_type: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[str] = Field(None, max_length=50)


class MachineResponse(MachineBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
