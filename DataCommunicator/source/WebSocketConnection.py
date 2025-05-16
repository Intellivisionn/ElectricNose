import asyncio
import json
import websockets
from abc import ABC, abstractmethod

class IDataConnection(ABC):
    """Interface for a bidirectional JSON connection."""

    @abstractmethod
    async def connect(self) -> None:
        ...

    @abstractmethod
    async def send(self, to: str, payload: dict) -> None:
        """
        If `to` starts with 'topic:', publish to a topic.
        Otherwise, send to a specific client.
        """
        ...

    @abstractmethod
    async def broadcast(self, payload: dict) -> None:
        """Send to all connected clients (no topic filtering)."""
        ...

    @abstractmethod
    async def subscribe(self, topic: str) -> None:
        """Subscribe this client to a topic."""
        ...

    @abstractmethod
    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribe this client from a topic."""
        ...

    @abstractmethod
    def set_client(self, client) -> None:
        """Bind the connection to a local BaseDataClient."""
        ...

class WebSocketConnection(IDataConnection):
    def __init__(self, uri: str):
        self.uri = uri
        self.ws = None
        self.client = None  # will be set via set_client()

    def set_client(self, client) -> None:
        self.client = client
        if not hasattr(client, 'name'):
            raise AttributeError("Client must have a 'name' attribute")
        self.name = client.name

    async def connect(self) -> None:
        self.ws = await websockets.connect(self.uri)
        # register with broker
        await self.ws.send(json.dumps({'type': 'register', 'name': self.client.name}))
        # start listener
        asyncio.create_task(self._listen())

    async def _listen(self) -> None:
        async for msg in self.ws:
            data = json.loads(msg)
            frm = data.get('from')
            payload = data.get('payload')
            # delegate to client
            await self.client.on_message(frm, payload)

    async def broadcast(self, payload: dict) -> None:
        packet = {'to': 'broadcast', 'from': self.client.name, 'payload': payload}
        await self.ws.send(json.dumps(packet))

    async def subscribe(self, topic: str):
        msg = {'type': 'subscribe', 'topic': topic, 'name': self.name}
        await self.ws.send(json.dumps(msg))

    async def unsubscribe(self, topic: str):
        msg = {'type': 'unsubscribe', 'topic': topic, 'name': self.name}
        await self.ws.send(json.dumps(msg))

    async def send(self, to: str, payload: dict):
        if isinstance(to, str) and to.startswith('topic:'):
            topic = to[6:]
            msg = {'type': 'publish', 'topic': topic, 'from': self.name, 'payload': payload}
        else:
            msg = {'to': to, 'from': self.name, 'payload': payload}
        await self.ws.send(json.dumps(msg))