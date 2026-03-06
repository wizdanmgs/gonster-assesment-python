from typing import List, Optional
import uuid
from app.models.machine import MachineMetadata
from app.schemas.machine import MachineCreate, MachineUpdate
from app.repositories.base import MachineRepository

async def create_machine(repo: MachineRepository, machine_in: MachineCreate) -> MachineMetadata:
    return await repo.create(machine_in)

async def get_machine(repo: MachineRepository, machine_id: uuid.UUID) -> Optional[MachineMetadata]:
    return await repo.get_by_id(machine_id)

async def get_machines(
    repo: MachineRepository, skip: int = 0, limit: int = 100
) -> List[MachineMetadata]:
    return await repo.get_all(skip, limit)

async def update_machine(
    repo: MachineRepository, db_machine: MachineMetadata, machine_in: MachineUpdate
) -> MachineMetadata:
    return await repo.update(db_machine, machine_in)

async def delete_machine(repo: MachineRepository, machine_id: uuid.UUID) -> bool:
    return await repo.delete(machine_id)

async def validate_machines_exist(repo: MachineRepository, machine_ids: List[uuid.UUID]) -> List[uuid.UUID]:
    """
    Validates that a list of machine IDs exist in the database.
    Returns a list of machine IDs that DO NOT exist.
    """
    return await repo.validate_exists(machine_ids)
