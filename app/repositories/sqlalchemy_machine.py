import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.machine import MachineMetadata
from app.repositories.base import MachineRepository
from app.schemas.machine import MachineCreate, MachineUpdate


class SqlAlchemyMachineRepository(MachineRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, machine_in: MachineCreate) -> MachineMetadata:
        db_machine = MachineMetadata(
            name=machine_in.name,
            location=machine_in.location,
            sensor_type=machine_in.sensor_type,
            status=machine_in.status,
        )
        self.db.add(db_machine)
        await self.db.commit()
        await self.db.refresh(db_machine)
        return db_machine

    async def get_by_id(self, machine_id: uuid.UUID) -> Optional[MachineMetadata]:
        result = await self.db.execute(
            select(MachineMetadata).where(MachineMetadata.id == machine_id)
        )
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[MachineMetadata]:
        result = await self.db.execute(
            select(MachineMetadata).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def update(
        self, db_machine: MachineMetadata, machine_in: MachineUpdate
    ) -> MachineMetadata:
        update_data = machine_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_machine, field, value)

        self.db.add(db_machine)
        await self.db.commit()
        await self.db.refresh(db_machine)
        return db_machine

    async def delete(self, machine_id: uuid.UUID) -> bool:
        db_machine = await self.get_by_id(machine_id)
        if not db_machine:
            return False
        await self.db.delete(db_machine)
        await self.db.commit()
        return True

    async def validate_exists(self, machine_ids: List[uuid.UUID]) -> List[uuid.UUID]:
        unique_ids = list(set(machine_ids))
        result = await self.db.execute(
            select(MachineMetadata.id).where(MachineMetadata.id.in_(unique_ids))
        )
        existing_ids = {row[0] for row in result.all()}
        invalid_ids = [m_id for m_id in unique_ids if m_id not in existing_ids]
        return invalid_ids
