import asyncio
import threading
from datetime import datetime
from DataCollector.source.storage.istorage import IStorage
from DataCommunicator.source.BaseDataClient import BaseDataClient
from DataCommunicator.source.WebSocketConnection import WebSocketConnection

class CommStorage(IStorage, BaseDataClient):
    def __init__(self, ws_uri: str = "ws://localhost:8765"):
        self.ws_connection = WebSocketConnection(ws_uri)
        super().__init__('data_collector', self.ws_connection)
        self.sensor_data_list = []
        self.data_length_to_send = 5

        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self._start_loop, daemon=True)
        self.loop_thread.start()

    def _start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def connect(self):
        """Initialize WebSocket connection"""
        print("[CommStorage] connect() called")
        await self.ws_connection.connect()
        print("[CommStorage] WebSocket connected")

    async def send_data(self):
        await self.connect()
        await self.ws_connection.send("topic:complete_data", self.sensor_data_list)
        print("[CommStorage] Data sent via WebSocket")

    def write(self, data: list) -> None:
        self.sensor_data_list = data
        print(f"[CommStorage] {len(self.sensor_data_list)} elements stored to list")
        if len(self.sensor_data_list) >= self.data_length_to_send:
            future = asyncio.run_coroutine_threadsafe(self.send_data(), self.loop)
            try:
                future.result()  # Optional: can omit if you don't want to block
            except Exception as e:
                print(f"[CommStorage] Error sending data: {e}")


    def set_filename(self, scent_name) -> None:
        # Not needed for WebSocket communication
        pass

    def run(self) -> None:
        pass

    def on_message(self, frm: str, payload: dict):
        pass