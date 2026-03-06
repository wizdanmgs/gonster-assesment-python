"""
MQTT Subscriber Service
-----------------------
Manages the lifecycle of a persistent, async MQTT connection using aiomqtt.
Designed to run as a background asyncio Task alongside the FastAPI server.
"""

import asyncio
import logging

import aiomqtt

from app.core.config import settings
from app.core.messages import (
    get_message,
    MSG_MQTT_CONNECTED,
    MSG_MQTT_DISCONNECTED,
)
from app.mqtt.base import MessageSubscriber
from app.mqtt.handler import handle_mqtt_message
from app.repositories.base import MachineRepository, SensorRepository

logger = logging.getLogger(__name__)

RECONNECT_DELAY_SECONDS = 5  # back-off between reconnection attempts


class MQTTSubscriberService(MessageSubscriber):
    """
    Async MQTT subscriber that connects to the configured broker, subscribes
    to the telemetry topic filter and forwards every incoming message to the
    central message handler.

    Usage (from FastAPI lifespan):

        service = MQTTSubscriberService(sensor_repo, machine_repo)
        task = asyncio.create_task(service.start())
        ...
        await service.stop()
        await task
    """

    def __init__(self, sensor_repo: SensorRepository, machine_repo: MachineRepository) -> None:
        self._sensor_repo = sensor_repo
        self._machine_repo = machine_repo
        self._stop_event = asyncio.Event()

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    async def start(self) -> None:
        """
        Connect to the broker, subscribe, and enter the message loop.
        Reconnects automatically on network errors until stop() is called.
        """
        while not self._stop_event.is_set():
            try:
                async with aiomqtt.Client(
                    hostname=settings.MQTT_BROKER_HOST,
                    port=settings.MQTT_BROKER_PORT,
                    identifier=settings.MQTT_CLIENT_ID,
                ) as client:
                    logger.info(
                        get_message(
                            MSG_MQTT_CONNECTED,
                            host=settings.MQTT_BROKER_HOST,
                            port=settings.MQTT_BROKER_PORT,
                            topic=settings.MQTT_TOPIC_FILTER,
                        )
                    )
                    # Subscribe to the wildcard telemetry topic
                    await client.subscribe(settings.MQTT_TOPIC_FILTER)

                    # Process incoming messages until stop() is called
                    async for message in client.messages:
                        if self._stop_event.is_set():
                            break
                        await handle_mqtt_message(
                            topic=str(message.topic),
                            payload=message.payload,
                            sensor_repo=self._sensor_repo,
                            machine_repo=self._machine_repo,
                        )

            except aiomqtt.MqttError as exc:
                if self._stop_event.is_set():
                    break
                logger.warning(
                    "MQTT connection lost (%s). Reconnecting in %d s…",
                    exc,
                    RECONNECT_DELAY_SECONDS,
                )
                await asyncio.sleep(RECONNECT_DELAY_SECONDS)

            except asyncio.CancelledError:
                logger.debug("MQTT subscriber task received cancellation.")
                break

            except Exception as exc:  # noqa: BLE001
                logger.error("Unexpected MQTT error: %s", exc, exc_info=True)
                if not self._stop_event.is_set():
                    await asyncio.sleep(RECONNECT_DELAY_SECONDS)

        logger.info(get_message(MSG_MQTT_DISCONNECTED))

    async def stop(self) -> None:
        """Signal the subscriber loop to exit after the current message."""
        self._stop_event.set()
