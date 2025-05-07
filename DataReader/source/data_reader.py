import threading
import time
import json
from datetime import datetime
import os

class SensorDataCollector:
    def __init__(self, sensor_json_file="/home/admin/ElectricNose/SensorReader/sensor_data.json", 
                 output_dir="savedData", read_interval=2, write_interval=5):
        # Shared data and synchronization
        self.sensor_data_list = []
        self.data_lock = threading.Lock()
        self.stop_event = threading.Event()

        self.sensor_json_file = sensor_json_file
        self.read_interval = read_interval
        self.write_interval = write_interval

        # Ask user for the scent name and create an output file name with current timestamp
        self.scent_name = input("What scent you want to save: ")
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.output_file = os.path.join(output_dir, f"{self.scent_name}_{current_time}.json")

        # Initialize threads as None; they'll be created in start()
        self.reader_thread = None
        self.writer_thread = None

    def start(self):
        # Create and start the sensor reader and writer threads
        self.reader_thread = self.SensorReaderThread(self)
        self.writer_thread = self.SensorWriterThread(self, self.output_file)
        self.reader_thread.start()
        self.writer_thread.start()

        try:
            # Keep the main thread alive until a KeyboardInterrupt is received
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Stopping data collection...")
            self.stop_event.set()  # Signal threads to stop
            self.reader_thread.join()
            self.writer_thread.join()
            print("Data collection stopped.")

    def read_sensor_data(self):
        """Reads the sensor JSON file and appends data with a timestamp."""
        try:
            with open(self.sensor_json_file, "r") as f:
                data = json.load(f)
            # Add a timestamp to the data
            data['timestamp'] = datetime.now().isoformat()
            with self.data_lock:
                self.sensor_data_list.append(data)
            print(f"Read sensor data at {data['timestamp']}")
        except Exception as e:
            print(f"Error reading JSON file: {e}")

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

    class SensorReaderThread(threading.Thread):
        def __init__(self, collector):
            super().__init__()
            self.collector = collector

        def run(self):
            while not self.collector.stop_event.is_set():
                self.collector.read_sensor_data()
                time.sleep(self.collector.read_interval)

    class SensorWriterThread(threading.Thread):
        def __init__(self, collector, output_file):
            super().__init__()
            self.collector = collector
            self.output_file = output_file

        def run(self):
            while not self.collector.stop_event.is_set():
                time.sleep(self.collector.write_interval)
                self.collector.write_sensor_data(self.output_file)

if __name__ == "__main__":
    collector = SensorDataCollector()
    collector.start()
