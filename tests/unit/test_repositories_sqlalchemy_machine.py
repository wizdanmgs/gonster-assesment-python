import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.machine import MachineMetadata
from app.repositories.sqlalchemy_machine import SqlAlchemyMachineRepository
from app.schemas.machine import MachineCreate


@pytest.fixture
def mock_db_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repository(mock_db_session):
    return SqlAlchemyMachineRepository(mock_db_session)


@pytest.mark.asyncio
async def test_create_machine(repository, mock_db_session):
    # Arrange
    machine_in = MachineCreate(
        name="Test Machine", location="Lab A", sensor_type="Temp", status="active"
    )

    # Act
    result = await repository.create(machine_in)

    # Assert
    assert result.name == machine_in.name
    assert result.location == machine_in.location
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_id(repository, mock_db_session):
    # Arrange
    machine_id = uuid.uuid4()
    mock_machine = MachineMetadata(id=machine_id, name="Test Machine")

    # Mocking the result of session.execute(select(...))
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_machine
    mock_db_session.execute.return_value = mock_result

    # Act
    result = await repository.get_by_id(machine_id)

    # Assert
    assert result == mock_machine
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_validate_exists_all_valid(repository, mock_db_session):
    # Arrange
    machine_ids = [uuid.uuid4(), uuid.uuid4()]

    # Mocking session.execute(...).all()
    mock_result = MagicMock()
    mock_result.all.return_value = [(machine_ids[0],), (machine_ids[1],)]
    mock_db_session.execute.return_value = mock_result

    # Act
    result = await repository.validate_exists(machine_ids)

    # Assert
    assert result == []  # All exist, so none are invalid
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_validate_exists_some_invalid(repository, mock_db_session):
    # Arrange
    machine_ids = [uuid.uuid4(), uuid.uuid4()]

    # Only machine_ids[0] exists
    mock_result = MagicMock()
    mock_result.all.return_value = [(machine_ids[0],)]
    mock_db_session.execute.return_value = mock_result

    # Act
    result = await repository.validate_exists(machine_ids)

    # Assert
    assert result == [machine_ids[1]]
    mock_db_session.execute.assert_called_once()
