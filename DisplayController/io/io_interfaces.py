from abc import ABC, abstractmethod

class IIOHandler(ABC):
    @abstractmethod
    async def start(self):
        """Start listening for buttons & control messages."""
        ...

    @abstractmethod
    async def stop(self):
        """Shutdown cleanly."""
        ...

    '''@abstractmethod
    def on_button_press(self, name: str):
        """Called when a hardware button is pressed."""
        ...

    @abstractmethod
    async def connect(self, uri: str):
        """Connect to the WebSocket at the given URI."""
        ...

    @abstractmethod
    async def send(self, topic: str, payload: dict):
        """Send an event out on the WebSocket."""
        ...'''

    @abstractmethod
    async def on_message(self, frm: str, payload: dict):
        """Invoked for every incoming WebSocket message."""
        ...