import sys
import threading
import time
import asyncio
from datetime import datetime

from DataCommunicator.source.WebSocketConnection import WebSocketConnection
from DataCommunicator.source.BaseDataClient   import BaseDataClient

from DataCollector.source.storage.json_storage import JSONStorage
from DataCollector.source.storage_manager import StorageManager



class SensorDataCollector:
    def __init__(self, scent_name: str = None, output_dir: str = "savedData"):
        self.sensor_data_list = []
        self.data_lock       = threading.Lock()
        self.stop_event      = threading.Event()

        # determine scent name
        if scent_name:
            self.scent_name = scent_name
        elif sys.stdin.isatty():
            self.scent_name = input("What scent you want to save: ")
        else:
            self.scent_name = "test_scent"

        # websocket receiver
        uri = 'ws://localhost:8765'
        self.ws_conn = WebSocketConnection(uri)
        self.receiver = self._ReceiverClient(self)

    def start(self, write_interval: float = 5.0):
        # 1) WebSocket receiver in background
        def _run_receiver():
            try:
                asyncio.run(self.receiver.start())
            except Exception as e:
                print(f"[Collector] Receiver error: {e}")
                self.stop_event.set()

        threading.Thread(target=_run_receiver, daemon=True).start()

        # 2) Only JSONStorage for now
        storages = [
            JSONStorage(),
            # CSVStorage(...)       # ← can plug in later
            # CloudStorage(...)     # ← can plug in later
        ]
        storage_mgr = StorageManager(storages, data_source=self, interval=write_interval, scent_name = self.scent_name)
        storage_mgr.start()

        # 3) keep main alive
        try:
            while not self.stop_event.is_set():
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Stopping data collection…")
            self.stop_event.set()
        finally:
            print("Data collection stopped.")

    class _ReceiverClient(BaseDataClient):
        def __init__(self, collector):
            super().__init__('collector', collector.ws_conn)
            self.collector = collector

        async def run(self):
            await self.connection.subscribe('sensor_readings')
            await asyncio.Future()  # run forever

        async def on_message(self, frm: str, payload: dict):
            payload['timestamp'] = datetime.now().isoformat()
            with self.collector.data_lock:
                self.collector.sensor_data_list.append(payload)
            print(f"[Collector] Received from {frm}: {payload}")


if __name__ == "__main__":
    scent_arg = sys.argv[1] if len(sys.argv) > 1 else None
    collector = SensorDataCollector(scent_name=scent_arg)
    collector.start(write_interval=5.0)
