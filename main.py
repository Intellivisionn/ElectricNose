import os
import time
import socket
import json
import hashlib

# Constants
JSON_FILE = "/home/admin/ElectricNose-SensorReader/sensor_data.json"
SOCKET_PORT = 9999
SOCKET_HOST = "localhost"
POLL_INTERVAL = 2  # seconds

def get_file_hash(filepath):
    """Generate hash of the file content for change detection."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def send_json_to_display(payload):
    """Send JSON payload to the display socket server."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SOCKET_HOST, SOCKET_PORT))
            s.sendall(json.dumps(payload).encode())
            print("Sent updated data to display.")
    except ConnectionRefusedError:
        print("Display socket not available. Is the display service running?")
    except Exception as e:
        print(f"Failed to send data: {e}")

def load_json(filepath):
    """Load JSON data from a file."""
    try:
        with open(filepath, "r") as file:
            return json.load(file)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return None

def format_as_display_payload(raw_data):
    """Transform raw sensor data into a display-friendly payload."""
    payload = {
        "title": "Sensor Readings",
        "lines": []
    }

    if isinstance(raw_data, list):
        raw_data = raw_data[0]

    if not isinstance(raw_data, dict):
        payload["title"] = "Invalid Sensor Format"
        return payload

    for sensor, readings in raw_data.items():
        payload["lines"].append({"text": f"{sensor}", "color": [30, 144, 255]})
        for key, value in readings.items():
            payload["lines"].append({
                "text": f"{key}: {value}",
                "color": [255, 255, 255]
            })

    return payload

def main():
    print("Starting sensor data monitor...")
    last_hash = None

    while True:
        current_hash = get_file_hash(JSON_FILE)

        if current_hash and current_hash != last_hash:
            print("Detected file change.")
            raw = load_json(JSON_FILE)
            if raw:
                payload = format_as_display_payload(raw)
                send_json_to_display(payload)
            last_hash = current_hash

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()