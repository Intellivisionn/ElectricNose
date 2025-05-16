from abc import ABC, abstractmethod

class BaseDataClient(ABC):
    """
    Abstract base for any named client.  Holds a IDataConnection,
    must implement run() and on_message().
    """
    def __init__(self, name: str, connection):
        self.name = name
        self.connection = connection
        self.connection.set_client(self)

    async def start(self) -> None:
        """Connect to broker and then begin client-specific run() loop."""
        await self.connection.connect()
        await self.run()

    @abstractmethod
    async def run(self) -> None:
        """Client-specific behavior loop."""
        ...

    @abstractmethod
    async def on_message(self, frm: str, payload: dict) -> None:
        """Handle an incoming message from another client."""
        ...
