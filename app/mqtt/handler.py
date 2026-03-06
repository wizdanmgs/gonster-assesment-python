"""
MQTT Message Handler
--------------------
Parses raw MQTT payloads, validates them against the existing Pydantic schemas,
verifies the machine exists in PostgreSQL, and persists the data to InfluxDB via
the SensorRepository interface.
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from app.core.messages import (
    get_message,
    MSG_MQTT_MESSAGE_RECEIVED,
    MSG_MQTT_PAYLOAD_INVALID,
    MSG_MQTT_MACHINE_NOT_FOUND,
    MSG_MQTT_INGEST_SUCCESS,
    MSG_MQTT_INGEST_FAILED,
)
from app.repositories.base import MachineRepository, SensorRepository
from app.schemas.sensor_data import BatchIngestRequest, SensorDataPayload, SensorMetrics

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
#  Internal helpers                                                            #
# --------------------------------------------------------------------------- #

def _extract_machine_id_from_topic(topic: str) -> uuid.UUID | None:
    """
    Extract the machine_id from an MQTT topic of the form:
        factory/<factory_id>/machine/<machine_id>/telemetry

    Returns a UUID object, or None if the topic structure is unexpected.
    """
    parts = topic.split("/")
    # Expected index positions: factory=0, factoryId=1, machine=2, machineId=3, telemetry=4
    if len(parts) != 5 or parts[2] != "machine" or parts[4] != "telemetry":
        logger.warning("Unexpected topic structure: %s", topic)
        return None
    try:
        return uuid.UUID(parts[3])
    except ValueError:
        logger.warning("Topic contains non-UUID machine segment: %s", parts[3])
        return None


def _parse_payload(raw: bytes) -> dict | None:
    """Decode and JSON-parse a raw MQTT payload. Returns None on failure."""
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        logger.error(get_message(MSG_MQTT_PAYLOAD_INVALID) + ": %s", exc)
        return None


def _build_sensor_payload(machine_id: uuid.UUID, data: dict) -> SensorDataPayload | None:
    """
    Build and validate a SensorDataPayload from raw dict data.
    Handles missing/null metric fields gracefully. Returns None if invalid.
    """
    try:
        # Allow the publisher to omit the machine_id in the JSON body;
        # it is authoritative from the MQTT topic.
        data.setdefault("machine_id", str(machine_id))
        data.setdefault("timestamp", datetime.now(timezone.utc).isoformat())

        metrics_raw = data.get("metrics", {})
        metrics = SensorMetrics(
            temperature=metrics_raw.get("temperature"),
            pressure=metrics_raw.get("pressure"),
            speed=metrics_raw.get("speed"),
        )
        return SensorDataPayload(
            machine_id=machine_id,
            timestamp=data["timestamp"],
            metrics=metrics,
        )
    except Exception as exc:
        logger.error(get_message(MSG_MQTT_PAYLOAD_INVALID) + ": %s", exc)
        return None


# --------------------------------------------------------------------------- #
#  Public handler                                                              #
# --------------------------------------------------------------------------- #

async def handle_mqtt_message(
    topic: str,
    payload: bytes,
    sensor_repo: SensorRepository,
    machine_repo: MachineRepository,
) -> None:
    """
    Central handler called for every MQTT message received by the subscriber.

    Steps:
    1. Extract machine_id from the MQTT topic wildcard segment.
    2. Decode + JSON-parse the raw payload bytes.
    3. Validate the payload against the SensorDataPayload schema.
    4. Verify the machine_id exists in PostgreSQL.
    5. Wrap the payload in a BatchIngestRequest and write to InfluxDB.

    All errors are caught and logged; the function never raises so the
    subscriber loop is never interrupted by a bad message.
    """
    logger.debug(get_message(MSG_MQTT_MESSAGE_RECEIVED, topic=topic))

    # Step 1 – extract machine_id from topic
    machine_id = _extract_machine_id_from_topic(topic)
    if machine_id is None:
        return

    # Step 2 – parse raw JSON payload
    data = _parse_payload(payload)
    if data is None:
        return

    # Step 3 – validate via Pydantic schema
    sensor_payload = _build_sensor_payload(machine_id, data)
    if sensor_payload is None:
        return

    # Step 4 – verify machine exists in PostgreSQL
    try:
        machine = await machine_repo.get_by_id(machine_id)
        if machine is None:
            logger.warning(get_message(MSG_MQTT_MACHINE_NOT_FOUND, machine_id=str(machine_id)))
            return
    except Exception as exc:
        logger.error("Failed to look up machine %s: %s", machine_id, exc)
        return

    # Step 5 – persist data to InfluxDB via the SensorRepository
    batch = BatchIngestRequest(gateway_id="mqtt-subscriber", payloads=[sensor_payload])
    try:
        await sensor_repo.write_batch(batch)
        logger.info(get_message(MSG_MQTT_INGEST_SUCCESS, machine_id=str(machine_id)))
    except Exception as exc:
        logger.error(get_message(MSG_MQTT_INGEST_FAILED, machine_id=str(machine_id)) + ": %s", exc)
