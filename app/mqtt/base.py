from abc import ABC, abstractmethod

class MessageSubscriber(ABC):
    """
    Abstract Base Class for message subscribers (MQTT, AMQP, etc.)
    Ensures a consistent interface for the application lifecycle.
    """

    @abstractmethod
    async def start(self) -> None:
        """
        Start the subscriber connection and message processing loop.
        Should be handled as a background task.
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """
        Signal the subscriber to stop and clean up resources.
        """
        pass
