import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.machine import MachineMetadata
from app.schemas.machine import MachineCreate, MachineUpdate
from app.schemas.sensor_data import BatchIngestRequest


class MachineRepository(ABC):
    @abstractmethod
    async def create(self, machine_in: MachineCreate) -> MachineMetadata:
        pass

    @abstractmethod
    async def get_by_id(self, machine_id: uuid.UUID) -> Optional[MachineMetadata]:
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[MachineMetadata]:
        pass

    @abstractmethod
    async def update(
        self, db_machine: MachineMetadata, machine_in: MachineUpdate
    ) -> MachineMetadata:
        pass

    @abstractmethod
    async def delete(self, machine_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    async def validate_exists(self, machine_ids: List[uuid.UUID]) -> List[uuid.UUID]:
        pass


class SensorRepository(ABC):
    @abstractmethod
    async def write_batch(self, batch: BatchIngestRequest) -> bool:
        pass

    @abstractmethod
    async def get_historical_data(
        self,
        machine_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
        interval: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        pass
