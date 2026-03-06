from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.messages import MSG_CREDENTIALS_INVALID, MSG_FORBIDDEN
from app.db.influx import get_influx_client
from app.db.postgres import get_db as get_sqlalchemy_db
from app.models.user import User, UserRole
from app.repositories.base import MachineRepository, SensorRepository
from app.repositories.influx_sensor import InfluxSensorRepository
from app.repositories.sqlalchemy_machine import SqlAlchemyMachineRepository
from app.schemas.user import TokenPayload


async def get_machine_repository(
    db: AsyncSession = Depends(get_sqlalchemy_db),
) -> MachineRepository:
    return SqlAlchemyMachineRepository(db)


async def get_sensor_repository(
    client: InfluxDBClientAsync = Depends(get_influx_client),
) -> SensorRepository:
    return InfluxSensorRepository(client)


reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

TokenDep = Annotated[str, Depends(reusable_oauth2)]
SessionDep = Annotated[AsyncSession, Depends(get_sqlalchemy_db)]


async def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        user = User(
            id=token_data.sub,
            role=token_data.role,
        )
    except (jwt.InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=MSG_CREDENTIALS_INVALID,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


class RoleChecker:
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: CurrentUser):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=MSG_FORBIDDEN,
            )
        return user
