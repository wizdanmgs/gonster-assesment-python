from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

from app.db.postgres import get_db as get_sqlalchemy_db
from app.db.influx import get_influx_client
from app.repositories.sqlalchemy_machine import SqlAlchemyMachineRepository
from app.repositories.influx_sensor import InfluxSensorRepository
from app.repositories.base import MachineRepository, SensorRepository

async def get_machine_repository(
    db: AsyncSession = Depends(get_sqlalchemy_db)
) -> MachineRepository:
    return SqlAlchemyMachineRepository(db)

async def get_sensor_repository(
    client: InfluxDBClientAsync = Depends(get_influx_client)
) -> SensorRepository:
    return InfluxSensorRepository(client)
