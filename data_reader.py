import threading
import time
import json
from datetime import datetime

# Shared list for sensor data and a lock for thread-safe operations
sensor_data_list = []
data_lock = threading.Lock()
stop_event = threading.Event()

def json_reader(json_file="sensor_data.json", interval=2):
    while not stop_event.is_set():
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
            # Add a timestamp to track when the reading was taken
            data['timestamp'] = datetime.now().isoformat()
            with data_lock:
                sensor_data_list.append(data)
            print(f"Read sensor data at {data['timestamp']}")
        except Exception as e:
            print(f"Error reading JSON file: {e}")
        time.sleep(interval)

def json_writer(json_file="saved_data.json", interval=5):
    """
    Thread function to write the cumulative sensor data to a JSON file.
    Writes to the file every `interval` seconds.
    """
    while not stop_event.is_set():
        time.sleep(interval)
        with data_lock:
            data_to_write = list(sensor_data_list)
        try:
            with open(json_file, "w") as f:
                json.dump(data_to_write, f, indent=4)
            print(f"Written {len(data_to_write)} sensor readings to {json_file}.")
        except Exception as e:
            print(f"Error writing to JSON file: {e}")

def main():
    # Create threads for reading sensor data and writing to JSON file
    reader_thread = threading.Thread(target=json_reader)
    writer_thread = threading.Thread(target=json_writer)
    
    reader_thread.start()
    writer_thread.start()

    try:
        # Keep the main thread alive until a KeyboardInterrupt is received
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopping data collection...")
        stop_event.set()  # Signal threads to stop
        reader_thread.join()
        writer_thread.join()
        print("Data collection stopped.")

if __name__ == "__main__":
    main()
