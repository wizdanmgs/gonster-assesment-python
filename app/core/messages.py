from typing import Any, Dict

# Message keys
MSG_SUCCESS = "SUCCESS"
MSG_ERROR = "ERROR"
MSG_VALIDATION_ERROR = "VALIDATION_ERROR"
MSG_NOT_FOUND = "NOT_FOUND"
MSG_INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"

# Machine-specific messages
MSG_MACHINE_REGISTERED = "MACHINE_REGISTERED"
MSG_MACHINES_RETRIEVED = "MACHINES_RETRIEVED"
MSG_MACHINE_DETAILS_RETRIEVED = "MACHINE_DETAILS_RETRIEVED"
MSG_MACHINE_UPDATED = "MACHINE_UPDATED"
MSG_MACHINE_DELETED = "MACHINE_DELETED"
MSG_MACHINE_NOT_FOUND = "MACHINE_NOT_FOUND"

# Ingest and Retrieval messages
MSG_INGEST_QUEUED = "INGEST_QUEUED"
MSG_HISTORICAL_DATA_RETRIEVED = "HISTORICAL_DATA_RETRIEVED"
MSG_INVALID_TIME_RANGE = "INVALID_TIME_RANGE"

# MQTT Subscriber messages
MSG_MQTT_CONNECTED = "MQTT_CONNECTED"
MSG_MQTT_DISCONNECTED = "MQTT_DISCONNECTED"
MSG_MQTT_MESSAGE_RECEIVED = "MQTT_MESSAGE_RECEIVED"
MSG_MQTT_PAYLOAD_INVALID = "MQTT_PAYLOAD_INVALID"
MSG_MQTT_MACHINE_NOT_FOUND = "MQTT_MACHINE_NOT_FOUND"
MSG_MQTT_INGEST_SUCCESS = "MQTT_INGEST_SUCCESS"
MSG_MQTT_INGEST_FAILED = "MQTT_INGEST_FAILED"

MESSAGES: Dict[str, str] = {
    MSG_SUCCESS: "Success",
    MSG_ERROR: "Error",
    MSG_VALIDATION_ERROR: "Invalid input data format or values.",
    MSG_NOT_FOUND: "Resource not found",
    MSG_INTERNAL_SERVER_ERROR: "An unexpected error occurred.",
    
    MSG_MACHINE_REGISTERED: "Machine registered successfully",
    MSG_MACHINES_RETRIEVED: "Machines retrieved successfully",
    MSG_MACHINE_DETAILS_RETRIEVED: "Machine details retrieved successfully",
    MSG_MACHINE_UPDATED: "Machine updated successfully",
    MSG_MACHINE_DELETED: "Machine deleted successfully",
    MSG_MACHINE_NOT_FOUND: "Machine not found",
    
    MSG_INGEST_QUEUED: "Successfully queued {count} data points for processing.",
    MSG_HISTORICAL_DATA_RETRIEVED: "Historical data retrieved successfully",
    MSG_INVALID_TIME_RANGE: "start_time must be strictly before end_time",

    MSG_MQTT_CONNECTED: "Connected to MQTT broker at {host}:{port}, subscribed to {topic}",
    MSG_MQTT_DISCONNECTED: "MQTT subscriber stopped.",
    MSG_MQTT_MESSAGE_RECEIVED: "MQTT message received on topic: {topic}",
    MSG_MQTT_PAYLOAD_INVALID: "Invalid MQTT payload — skipping message",
    MSG_MQTT_MACHINE_NOT_FOUND: "Machine {machine_id} not found in registry — discarding MQTT message",
    MSG_MQTT_INGEST_SUCCESS: "MQTT data for machine {machine_id} written to InfluxDB",
    MSG_MQTT_INGEST_FAILED: "Failed to write MQTT data for machine {machine_id} to InfluxDB",
}

def get_message(key: str, **kwargs: Any) -> str:
    """
    Get a message by key from the central repository.
    Supports basic string formatting using keyword arguments.
    """
    msg = MESSAGES.get(key, key)
    if kwargs:
        try:
            return msg.format(**kwargs)
        except (KeyError, ValueError):
            return msg
    return msg
