import asyncio
from datetime import datetime
from DataCollector.source.storage.istorage import IStorage
from DataCommunicator.source.WebSocketConnection import WebSocketConnection

class CommStorage(IStorage):
    def __init__(self, ws_uri: str = "ws://localhost:8765"):
        self.ws_connection = WebSocketConnection(ws_uri)
        self.loop = asyncio.get_event_loop()

    async def connect(self):
        """Initialize WebSocket connection"""
        await self.ws_connection.connect()
        print("[CommStorage] WebSocket connected")

    def write(self, data: list) -> None:
        try:
            # Send to WebSocket
            asyncio.run_coroutine_threadsafe(
                self.ws_connection.send("topic:completedata", data),
                self.loop
            )
            print(f"[CommStorage] Sent {len(data)} records to completedata topic")
        except Exception as e:
            print(f"[CommStorage] Send error: {e}")

    def set_filename(self, scent_name) -> None:
        # Not needed for WebSocket communication
        pass