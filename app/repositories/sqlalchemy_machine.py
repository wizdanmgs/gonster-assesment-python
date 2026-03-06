import asyncio
import json
import uuid
from typing import List, Optional

import structlog
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.cache import get_cache
from app.core.config import settings
from app.models.machine import MachineMetadata
from app.repositories.base import MachineRepository
from app.schemas.machine import MachineCreate, MachineUpdate

logger = structlog.get_logger(__name__)


class SqlAlchemyMachineRepository(MachineRepository):
    CACHE_KEY_PREFIX = "machine:"
    CACHE_EXPIRATION = 3600  # 1 hour

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

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                await self.db.commit()
                await self.db.refresh(db_machine)
                return db_machine
            except OperationalError as e:
                await self.db.rollback()
                if attempt == max_retries:
                    logger.error(
                        f"{settings.DB_ENGINE} persistence failed permanently",
                        machine_id=str(db_machine.id)
                        if hasattr(db_machine, "id") and db_machine.id
                        else None,
                        retries_exhausted=True,
                        total_attempts=max_retries,
                        error=f"{type(e).__name__}: {str(e)}",
                        action="Data point dropped or pushed to DLQ",
                    )
                    raise
                await asyncio.sleep(1)

    async def get_by_id(self, machine_id: uuid.UUID) -> Optional[MachineMetadata]:
        cache_client = get_cache()
        cache_key = f"{self.CACHE_KEY_PREFIX}{machine_id}"

        if cache_client:
            cached_data = await cache_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                # Create a simple mapping to MachineMetadata-like object or construct it directly if appropriate
                # Easiest way is to instantiate the SQLAlchemy model without attaching to session for read-only
                model = MachineMetadata(**data)
                return model

        result = await self.db.execute(
            select(MachineMetadata).where(MachineMetadata.id == machine_id)
        )
        db_machine = result.scalars().first()

        if db_machine and cache_client:
            # Pydantic json serializable dict
            machine_dict = {
                "id": str(db_machine.id),
                "name": db_machine.name,
                "location": db_machine.location,
                "sensor_type": db_machine.sensor_type,
                "status": db_machine.status,
                "created_at": db_machine.created_at.isoformat()
                if db_machine.created_at
                else None,
                "updated_at": db_machine.updated_at.isoformat()
                if db_machine.updated_at
                else None,
            }
            await cache_client.setex(
                cache_key, self.CACHE_EXPIRATION, json.dumps(machine_dict)
            )

        return db_machine

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

        # Invalidate cache
        cache_client = get_cache()
        if cache_client:
            await cache_client.delete(f"{self.CACHE_KEY_PREFIX}{db_machine.id}")

        return db_machine

    async def delete(self, machine_id: uuid.UUID) -> bool:
        db_machine = await self.get_by_id(machine_id)
        if not db_machine:
            return False
        await self.db.delete(db_machine)
        await self.db.commit()

        # Invalidate cache
        cache_client = get_cache()
        if cache_client:
            await cache_client.delete(f"{self.CACHE_KEY_PREFIX}{machine_id}")

        return True

    async def validate_exists(self, machine_ids: List[uuid.UUID]) -> List[uuid.UUID]:
        unique_ids = list(set(machine_ids))
        existing_ids = set()
        missing_ids_from_cache = []

        cache_client = get_cache()

        if cache_client:
            # Check cache for each ID first, or use mget
            cache_keys = [f"{self.CACHE_KEY_PREFIX}{mid}" for mid in unique_ids]
            cached_values = await cache_client.mget(cache_keys)

            for mid, c_val in zip(unique_ids, cached_values):
                if c_val:
                    existing_ids.add(mid)
                else:
                    missing_ids_from_cache.append(mid)
        else:
            missing_ids_from_cache = unique_ids

        if missing_ids_from_cache:
            result = await self.db.execute(
                select(MachineMetadata.id).where(
                    MachineMetadata.id.in_(missing_ids_from_cache)
                )
            )
            db_existing = {row[0] for row in result.all()}
            existing_ids.update(db_existing)

            # Note: We won't automatically cache them all here since we only have IDs,
            # unless we query the full objects, which breaks the optimization here.
            # get_by_id caches the entire object when requested.

        invalid_ids = [m_id for m_id in unique_ids if m_id not in existing_ids]
        return invalid_ids
