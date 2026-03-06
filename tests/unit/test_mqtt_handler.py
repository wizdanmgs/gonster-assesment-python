"""
Unit tests for app.mqtt.handler.handle_mqtt_message

All external dependencies (machine_repo, sensor_repo) are replaced with
AsyncMock objects so no real database or broker is needed.
"""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.models.machine import MachineMetadata
from app.mqtt.handler import handle_mqtt_message

# ── Helpers ──────────────────────────────────────────────────────────────── #


def _make_repos(machine_exists: bool = True):
    """Return a pair of (sensor_repo_mock, machine_repo_mock)."""
    machine_repo = AsyncMock()
    sensor_repo = AsyncMock()

    if machine_exists:
        machine_repo.get_by_id.return_value = MachineMetadata(
            id=uuid.uuid4(),
            name="Test Machine",
            location="Factory A",
            sensor_type="Thermal",
        )
    else:
        machine_repo.get_by_id.return_value = None

    sensor_repo.write_batch.return_value = True
    return sensor_repo, machine_repo


def _valid_payload(machine_id: uuid.UUID) -> bytes:
    return json.dumps(
        {
            "machine_id": str(machine_id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {"temperature": 72.5, "pressure": 3.2, "speed": None},
        }
    ).encode()


def _topic(machine_id: uuid.UUID) -> str:
    return f"factory/A/machine/{machine_id}/telemetry"


# ── Tests ─────────────────────────────────────────────────────────────────── #


@pytest.mark.asyncio
async def test_handle_valid_payload():
    """A well-formed message from a registered machine should be written to InfluxDB."""
    machine_id = uuid.uuid4()
    sensor_repo, machine_repo = _make_repos(machine_exists=True)

    await handle_mqtt_message(
        topic=_topic(machine_id),
        payload=_valid_payload(machine_id),
        sensor_repo=sensor_repo,
        machine_repo=machine_repo,
    )

    machine_repo.get_by_id.assert_called_once_with(machine_id)
    sensor_repo.write_batch.assert_called_once()


@pytest.mark.asyncio
async def test_handle_invalid_json():
    """A message with malformed JSON must be silently discarded without raising."""
    machine_id = uuid.uuid4()
    sensor_repo, machine_repo = _make_repos()

    await handle_mqtt_message(
        topic=_topic(machine_id),
        payload=b"this is not json",
        sensor_repo=sensor_repo,
        machine_repo=machine_repo,
    )

    machine_repo.get_by_id.assert_not_called()
    sensor_repo.write_batch.assert_not_called()


@pytest.mark.asyncio
async def test_handle_machine_not_found():
    """A message for an unregistered machine must be discarded."""
    machine_id = uuid.uuid4()
    sensor_repo, machine_repo = _make_repos(machine_exists=False)

    await handle_mqtt_message(
        topic=_topic(machine_id),
        payload=_valid_payload(machine_id),
        sensor_repo=sensor_repo,
        machine_repo=machine_repo,
    )

    machine_repo.get_by_id.assert_called_once_with(machine_id)
    sensor_repo.write_batch.assert_not_called()


@pytest.mark.asyncio
async def test_handle_missing_metrics():
    """All-null metrics should fail SensorDataPayload validation; message is discarded."""
    machine_id = uuid.uuid4()
    sensor_repo, machine_repo = _make_repos()

    bad_payload = json.dumps(
        {
            "machine_id": str(machine_id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {"temperature": None, "pressure": None, "speed": None},
        }
    ).encode()

    await handle_mqtt_message(
        topic=_topic(machine_id),
        payload=bad_payload,
        sensor_repo=sensor_repo,
        machine_repo=machine_repo,
    )

    # Schema validation error is caught within the handler; nothing should be written
    sensor_repo.write_batch.assert_not_called()


@pytest.mark.asyncio
async def test_handle_unexpected_topic_shape():
    """Messages on a badly structured topic are dropped before any repo is called."""
    sensor_repo, machine_repo = _make_repos()

    await handle_mqtt_message(
        topic="some/random/topic",
        payload=b"{}",
        sensor_repo=sensor_repo,
        machine_repo=machine_repo,
    )

    machine_repo.get_by_id.assert_not_called()
    sensor_repo.write_batch.assert_not_called()


@pytest.mark.asyncio
async def test_handle_non_uuid_machine_segment():
    """A topic whose machine segment is not a UUID is silently dropped."""
    sensor_repo, machine_repo = _make_repos()

    await handle_mqtt_message(
        topic="factory/A/machine/not-a-uuid/telemetry",
        payload=b"{}",
        sensor_repo=sensor_repo,
        machine_repo=machine_repo,
    )

    machine_repo.get_by_id.assert_not_called()
    sensor_repo.write_batch.assert_not_called()
