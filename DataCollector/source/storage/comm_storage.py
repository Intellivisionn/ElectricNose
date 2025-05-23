import asyncio
from datetime import datetime
from DataCollector.source.storage.istorage import IStorage
from DataCommunicator.source.WebSocketConnection import WebSocketConnection

class CommStorage(IStorage):
    def __init__(self, ws_uri: str = "ws://localhost:8765"):
        self.ws_connection = WebSocketConnection(ws_uri)
        self.loop = asyncio.get_event_loop()
        self.sensor_data_list = []
        self.data_lenght_to_send = 90

    async def connect(self):
        """Initialize WebSocket connection"""
        await self.ws_connection.connect()
        print("[CommStorage] WebSocket connected")

    def write(self, data: list) -> None:
        self.sensor_data_list = data
        print(f"[CommStorage] {len(self.sensor_data_list)} elements stored to list")
        if len(self.sensor_data_list) >= self.data_lenght_to_send:
            self.connect()
            self.ws_connection.send("topic:complete_data", self.sensor_data_list)

    def set_filename(self, scent_name) -> None:
        # Not needed for WebSocket communication
        pass