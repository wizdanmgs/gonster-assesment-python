import uuid
import pytest
from unittest.mock import AsyncMock
from app.services import machine as machine_service
from app.schemas.machine import MachineCreate, MachineUpdate
from app.models.machine import MachineMetadata

@pytest.mark.asyncio
async def test_create_machine():
    # Arrange
    mock_repo = AsyncMock()
    machine_in = MachineCreate(name="Test Machine", sensor_type="Sensor", location="Test Lab")
    expected_machine = MachineMetadata(
        id=uuid.uuid4(),
        name=machine_in.name,
        sensor_type=machine_in.sensor_type,
        location=machine_in.location
    )
    mock_repo.create.return_value = expected_machine

    # Act
    result = await machine_service.create_machine(mock_repo, machine_in)

    # Assert
    assert result == expected_machine
    mock_repo.create.assert_called_once_with(machine_in)

@pytest.mark.asyncio
async def test_get_machine():
    # Arrange
    mock_repo = AsyncMock()
    machine_id = uuid.uuid4()
    expected_machine = MachineMetadata(
        id=machine_id,
        name="Test Machine",
        sensor_type="Sensor",
        location="Test Lab"
    )
    mock_repo.get_by_id.return_value = expected_machine

    # Act
    result = await machine_service.get_machine(mock_repo, machine_id)

    # Assert
    assert result == expected_machine
    mock_repo.get_by_id.assert_called_once_with(machine_id)

@pytest.mark.asyncio
async def test_get_machine_not_found():
    # Arrange
    mock_repo = AsyncMock()
    machine_id = uuid.uuid4()
    mock_repo.get_by_id.return_value = None

    # Act
    result = await machine_service.get_machine(mock_repo, machine_id)

    # Assert
    assert result is None
    mock_repo.get_by_id.assert_called_once_with(machine_id)

@pytest.mark.asyncio
async def test_validate_machines_exist():
    # Arrange
    mock_repo = AsyncMock()
    machine_ids = [uuid.uuid4(), uuid.uuid4()]
    non_existent_ids = [machine_ids[1]]
    mock_repo.validate_exists.return_value = non_existent_ids

    # Act
    result = await machine_service.validate_machines_exist(mock_repo, machine_ids)

    # Assert
    assert result == non_existent_ids
    mock_repo.validate_exists.assert_called_once_with(machine_ids)
