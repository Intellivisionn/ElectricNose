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
        ...

    @abstractmethod
    async def broadcast(self, payload: dict) -> None:
        ...

    @abstractmethod
    def set_client(self, client) -> None:
        ...

class WebSocketConnection(IDataConnection):
    def __init__(self, uri: str):
        self.uri = uri
        self.ws = None
        self.client = None  # will be set via set_client()

    def set_client(self, client) -> None:
        self.client = client

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

    async def send(self, to: str, payload: dict) -> None:
        packet = {'to': to, 'from': self.client.name, 'payload': payload}
        await self.ws.send(json.dumps(packet))

    async def broadcast(self, payload: dict) -> None:
        packet = {'to': 'broadcast', 'from': self.client.name, 'payload': payload}
        await self.ws.send(json.dumps(packet))