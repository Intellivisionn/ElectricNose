import sys, os
# insert project root (one level up from DataCollector/source) onto PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))

import threading
import time
import json
from datetime import datetime
import os
import sys
import asyncio

from DataCommunicator.source.WebSocketConnection import WebSocketConnection
from DataCommunicator.source.BaseDataClient import BaseDataClient

class SensorDataCollector:
    def __init__(
        self,
        scent_name=None,
        output_dir="savedData",
        write_interval=5
    ):
        # Shared data and synchronization
        self.sensor_data_list = []
        self.data_lock = threading.Lock()
        self.stop_event = threading.Event()

        # Determine scent name
        if scent_name is None:
            if sys.stdin.isatty():
                self.scent_name = input("What scent you want to save: ")
            else:
                self.scent_name = "test_scent"
        else:
            self.scent_name = scent_name


        # Prepare output file path
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(output_dir, exist_ok=True)
        self.output_file = os.path.join(output_dir, f"{self.scent_name}_{current_time}.json")

        # DataCommunicator client setup
        uri = 'ws://localhost:8765'
        self.ws_conn = WebSocketConnection(uri)
        self.receiver = self._ReceiverClient(self)

        # Writer settings
        self.write_interval = write_interval
        self.writer_thread = None

    def start(self):
        # Receiver wrapper that catches connection errors
        def _run_receiver():
            try:
                asyncio.run(self.receiver.start())
            except Exception as e:
                print(f"[collector] Receiver error: {e}")
                # signal shutdown
                self.stop_event.set()

        # Start the WebSocket receiver in a background thread
        receiver_thread = threading.Thread(
            target=_run_receiver,
            daemon=True
        )
        receiver_thread.start()

        # Start the writer thread
        self.writer_thread = self.SensorWriterThread(self, self.output_file, self.write_interval)
        self.writer_thread.start()

        try:
            # Keep main thread alive until stop_event or Ctrl-C
            while not self.stop_event.is_set():
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Stopping data collection...")
            self.stop_event.set()
        finally:
            # Ensure both threads are joined
            receiver_thread.join()
            self.writer_thread.join()
            print("Data collection stopped.")

    def write_sensor_data(self, output_file):
        """Writes the cumulative sensor data to the specified JSON file."""
        with self.data_lock:
            data_to_write = list(self.sensor_data_list)
        try:
            with open(output_file, "w") as f:
                json.dump(data_to_write, f, indent=4)
            print(f"Written {len(data_to_write)} sensor readings to {output_file}.")
        except Exception as e:
            print(f"Error writing to JSON file: {e}")

    class SensorWriterThread(threading.Thread):
        def __init__(self, collector, output_file, write_interval):
            super().__init__()
            self.collector = collector
            self.output_file = output_file
            self.write_interval = write_interval

        def run(self):
            while not self.collector.stop_event.is_set():
                time.sleep(self.write_interval)
                self.collector.write_sensor_data(self.output_file)

    class _ReceiverClient(BaseDataClient):
        """
        Receives sensor payloads via DataCommunicator and appends
        them to the collector’s list.
        """
        def __init__(self, collector):
            super().__init__('collector', collector.ws_conn)
            self.collector = collector

        async def run(self):
            await self.connection.subscribe('sensor_readings')
            # Keep the WebSocket connection alive indefinitely
            await asyncio.Future()

        async def on_message(self, frm: str, payload: dict):
            # Add a timestamp and store
            payload['timestamp'] = datetime.now().isoformat()
            with self.collector.data_lock:
                self.collector.sensor_data_list.append(payload)
            print(f"[collector] Received data from {frm}: {payload}")


if __name__ == "__main__":
    scent_arg = sys.argv[1] if len(sys.argv) >= 2 else None
    collector = SensorDataCollector(scent_name=scent_arg)
    collector.start()