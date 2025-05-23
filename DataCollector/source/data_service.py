import sys
import os
import threading
import time
import asyncio
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))

from DataCommunicator.source.WebSocketConnection import WebSocketConnection
from DataCommunicator.source.BaseDataClient import BaseDataClient
from DataCollector.source.storage.json_storage import JSONStorage
from DataCollector.source.storage.comm_storage import CommStorage
from DataCollector.source.storage_manager import StorageManager

class SensorDataCollector(BaseDataClient):
    def __init__(self, uri: str = 'ws://localhost:8765'):
        super().__init__('collector', WebSocketConnection(uri))
        self.sensor_data_list = []
        self.data_lock = threading.Lock()
        self.collecting = False
        self._state_q = asyncio.Queue()
        
        # Storage setup
        self.json_storage = JSONStorage()
        self.comm_storage = CommStorage(uri)
        
    async def start(self):
        await self.connection.connect()
        print("[Collector] Connected")
        return await super().start()

    async def run(self):
        # Subscribe to both sensor readings and state
        await self.connection.subscribe('sensor_readings')
        await self.connection.subscribe('state')
        print("[Collector] Subscribed to sensor_readings and state")

        # Start collection loop
        asyncio.create_task(self._collection_loop())

        # Keep alive
        while True:
            await asyncio.sleep(1)

    async def on_message(self, topic: str, payload: dict):
        if topic == 'state':
            state = payload.get('state')
            if state:
                print(f"[Collector] Got state → {state}")
                await self._state_q.put(state)
        
        elif topic == 'sensor_readings' and self.collecting:
            payload['timestamp'] = datetime.now().isoformat()
            with self.data_lock:
                self.sensor_data_list.append(payload)
            print(f"[Collector] Received data: {payload}")

    async def _collection_loop(self):
        while True:
            # Wait for LoadingState
            state = await self._state_q.get()
            if state != "LoadingState":
                continue

            print("[Collector] Starting collection")
            self.collecting = True
            self.sensor_data_list = []  # Clear previous data
            
            # Set filename for JSON storage
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.json_storage.set_filename(f"collection_{ts}")

            # Wait for PredictingState
            while True:
                state = await self._state_q.get()
                if state == "PredictingState":
                    break

            print("[Collector] Stopping collection")
            self.collecting = False

            # Save collected data
            with self.data_lock:
                if self.sensor_data_list:
                    # Write to JSON file
                    self.json_storage.write(self.sensor_data_list)
                    
                    # Send to WebSocket for 10 seconds
                    t_end = asyncio.get_event_loop().time() + 10.0
                    while asyncio.get_event_loop().time() < t_end:
                        await self.comm_storage.write(self.sensor_data_list)
                        await asyncio.sleep(0.5)

            print("[Collector] Data saved and sent")

            # Clear state queue until we leave PredictingState
            while True:
                new_state = await self._state_q.get()
                if new_state != "PredictingState":
                    break

if __name__ == "__main__":
    async def main():
        collector = SensorDataCollector()
        await collector.start()

    asyncio.run(main())