import uuid
import pytest
from unittest.mock import AsyncMock
from fastapi import status
from app.api.deps import get_machine_repository
from app.schemas.machine import MachineResponse
from app.models.machine import MachineMetadata
from app.core.messages import (
    get_message,
    MSG_MACHINE_REGISTERED,
    MSG_MACHINES_RETRIEVED
)

@pytest.fixture
def mock_machine_repo():
    return AsyncMock()

@pytest.mark.asyncio
async def test_register_machine_endpoint(client, app, mock_machine_repo):
    # Arrange
    app.dependency_overrides[get_machine_repository] = lambda: mock_machine_repo
    
    machine_data = {
        "name": "Injection Molder 5",
        "location": "Aisle 4",
        "sensor_type": "Pressure",
        "status": "active"
    }
    
    mock_machine = MachineMetadata(
        id=uuid.uuid4(),
        **machine_data
    )
    mock_machine_repo.create.return_value = mock_machine

    # Act
    response = await client.post("/api/v1/machines/", json=machine_data)

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["message"] == get_message(MSG_MACHINE_REGISTERED)
    assert data["data"]["name"] == machine_data["name"]
    mock_machine_repo.create.assert_called_once()
    
    # Cleanup
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_list_machines_endpoint(client, app, mock_machine_repo):
    # Arrange
    app.dependency_overrides[get_machine_repository] = lambda: mock_machine_repo
    
    mock_machines = [
        MachineMetadata(id=uuid.uuid4(), name="Machine 1", location="Loc 1", sensor_type="Type 1", status="active"),
        MachineMetadata(id=uuid.uuid4(), name="Machine 2", location="Loc 2", sensor_type="Type 2", status="active")
    ]
    mock_machine_repo.get_all.return_value = mock_machines

    # Act
    response = await client.get("/api/v1/machines/")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == get_message(MSG_MACHINES_RETRIEVED)
    assert len(data["data"]) == 2
    assert data["data"][0]["name"] == "Machine 1"
    mock_machine_repo.get_all.assert_called_once()
    
    # Cleanup
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_machine_not_found_endpoint(client, app, mock_machine_repo):
    # Arrange
    app.dependency_overrides[get_machine_repository] = lambda: mock_machine_repo
    mock_machine_repo.get_by_id.return_value = None
    machine_id = uuid.uuid4()

    # Act
    response = await client.get(f"/api/v1/machines/{machine_id}")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # Cleanup
    app.dependency_overrides.clear()
