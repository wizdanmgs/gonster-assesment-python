import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import status

from app.api.deps import get_current_user, get_machine_repository, get_sensor_repository
from app.core.messages import MSG_INGEST_QUEUED, MSG_MACHINE_NOT_FOUND, get_message
from app.enums.role import UserRole
from app.models.user import User


@pytest.fixture
def mock_machine_repo():
    return AsyncMock()


@pytest.fixture
def mock_sensor_repo():
    return AsyncMock()


@pytest.fixture
def mock_user():
    return User(id=uuid.uuid4(), role=UserRole.OPERATOR)


@pytest.mark.asyncio
async def test_ingest_sensor_data_success(
    client, app, mock_machine_repo, mock_sensor_repo, mock_user
):
    # Arrange
    app.dependency_overrides[get_machine_repository] = lambda: mock_machine_repo
    app.dependency_overrides[get_sensor_repository] = lambda: mock_sensor_repo
    app.dependency_overrides[get_current_user] = lambda: mock_user

    machine_id = uuid.uuid4()
    mock_machine_repo.validate_exists.return_value = []  # No invalid IDs
    mock_sensor_repo.write_batch.return_value = True

    payload = {
        "gateway_id": "gateway_123",
        "payloads": [
            {
                "machine_id": str(machine_id),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": {"temperature": 25.5, "pressure": 1.2, "speed": 1500},
            }
        ],
    }

    # Act
    response = await client.post("/api/v1/data/ingest", json=payload)

    # Assert
    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert data["message"] == get_message(MSG_INGEST_QUEUED, count=1)
    mock_machine_repo.validate_exists.assert_called_once()
    mock_sensor_repo.write_batch.assert_called_once()

    # Cleanup
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ingest_sensor_data_invalid_machine(
    client, app, mock_machine_repo, mock_sensor_repo, mock_user
):
    # Arrange
    app.dependency_overrides[get_machine_repository] = lambda: mock_machine_repo
    app.dependency_overrides[get_sensor_repository] = lambda: mock_sensor_repo
    app.dependency_overrides[get_current_user] = lambda: mock_user

    machine_id = uuid.uuid4()
    mock_machine_repo.validate_exists.return_value = [
        machine_id
    ]  # Machine doesn't exist

    payload = {
        "gateway_id": "gateway_123",
        "payloads": [
            {
                "machine_id": str(machine_id),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": {"temperature": 25.5},
            }
        ],
    }

    # Act
    response = await client.post("/api/v1/data/ingest", json=payload)

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert MSG_MACHINE_NOT_FOUND in response.json()["message"]

    # Cleanup
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ingest_sensor_data_invalid_gateway_id(client, app, mock_user):
    # Arrange
    app.dependency_overrides[get_current_user] = lambda: mock_user

    payload = {
        "gateway_id": "invalid@gateway!",
        "payloads": [
            {
                "machine_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": {"temperature": 25.5},
            }
        ],
    }

    # Act
    response = await client.post("/api/v1/data/ingest", json=payload)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Cleanup
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ingest_sensor_data_future_timestamp(client, app, mock_user):
    # Arrange
    app.dependency_overrides[get_current_user] = lambda: mock_user

    future_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    payload = {
        "gateway_id": "gateway_123",
        "payloads": [
            {
                "machine_id": str(uuid.uuid4()),
                "timestamp": future_time.isoformat(),
                "metrics": {"temperature": 25.5},
            }
        ],
    }

    # Act
    response = await client.post("/api/v1/data/ingest", json=payload)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "future" in response.text

    # Cleanup
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ingest_sensor_data_old_timestamp(client, app, mock_user):
    # Arrange
    app.dependency_overrides[get_current_user] = lambda: mock_user

    old_time = datetime.now(timezone.utc) - timedelta(days=8)
    payload = {
        "gateway_id": "gateway_123",
        "payloads": [
            {
                "machine_id": str(uuid.uuid4()),
                "timestamp": old_time.isoformat(),
                "metrics": {"temperature": 25.5},
            }
        ],
    }

    # Act
    response = await client.post("/api/v1/data/ingest", json=payload)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert "too old" in response.text

    # Cleanup
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ingest_sensor_data_out_of_threshold(client, app, mock_user):
    # Arrange
    app.dependency_overrides[get_current_user] = lambda: mock_user

    payload = {
        "gateway_id": "gateway_123",
        "payloads": [
            {
                "machine_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": {"temperature": 600},  # Threshold is 500
            }
        ],
    }

    # Act
    response = await client.post("/api/v1/data/ingest", json=payload)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Cleanup
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ingest_sensor_data_batch_size_limit(client, app, mock_user):
    # Arrange
    app.dependency_overrides[get_current_user] = lambda: mock_user

    # More than 1000 payloads
    payloads = [
        {
            "machine_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {"temperature": 25.5},
        }
        for _ in range(1001)
    ]

    payload = {
        "gateway_id": "gateway_123",
        "payloads": payloads,
    }

    # Act
    response = await client.post("/api/v1/data/ingest", json=payload)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Cleanup
    app.dependency_overrides.clear()
