import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.machine import MachineMetadata
from app.schemas.machine import MachineCreate, MachineUpdate

async def create_machine(db: AsyncSession, machine_in: MachineCreate) -> MachineMetadata:
    db_machine = MachineMetadata(
        name=machine_in.name,
        location=machine_in.location,
        sensor_type=machine_in.sensor_type,
        status=machine_in.status
    )
    db.add(db_machine)
    await db.commit()
    await db.refresh(db_machine)
    return db_machine

async def get_machine(db: AsyncSession, machine_id: uuid.UUID) -> Optional[MachineMetadata]:
    result = await db.execute(select(MachineMetadata).where(MachineMetadata.id == machine_id))
    return result.scalars().first()

async def get_machines(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[MachineMetadata]:
    result = await db.execute(select(MachineMetadata).offset(skip).limit(limit))
    return result.scalars().all()

async def update_machine(
    db: AsyncSession, db_machine: MachineMetadata, machine_in: MachineUpdate
) -> MachineMetadata:
    update_data = machine_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_machine, field, value)
    
    db.add(db_machine)
    await db.commit()
    await db.refresh(db_machine)
    return db_machine

async def delete_machine(db: AsyncSession, machine_id: uuid.UUID) -> bool:
    db_machine = await get_machine(db, machine_id)
    if not db_machine:
        return False
    await db.delete(db_machine)
    await db.commit()
    return True

async def validate_machines_exist(db: AsyncSession, machine_ids: List[uuid.UUID]) -> List[uuid.UUID]:
    """
    Validates that a list of machine IDs exist in the database.
    Returns a list of machine IDs that DO NOT exist.
    """
    # Use a set to avoid duplicates and improve lookup speed
    unique_ids = list(set(machine_ids))
    
    result = await db.execute(
        select(MachineMetadata.id).where(MachineMetadata.id.in_(unique_ids))
    )
    existing_ids = {row[0] for row in result.all()}
    
    invalid_ids = [m_id for m_id in unique_ids if m_id not in existing_ids]
    return invalid_ids
