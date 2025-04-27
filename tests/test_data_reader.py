import pytest
import json
import threading
import time
from datetime import datetime
from unittest.mock import patch
from source.data_reader import SensorDataCollector

class TestSensorDataCollector:

    def test_read_sensor_data(self, tmp_path):
        # This test was previously discussed.
        sensor_data_file = tmp_path / "sensor_data.json"
        sensor_data_file.write_text(json.dumps({"sensor_value": 42}))

        with patch("builtins.input", return_value="test_scent"):
            collector = SensorDataCollector(sensor_json_file=str(sensor_data_file))

        collector.read_sensor_data()

        # Assert that one sensor reading was added.
        assert len(collector.sensor_data_list) == 1, "Expected one sensor data entry"
        data_entry = collector.sensor_data_list[0]

        # Verify the sensor value and the presence of a timestamp.
        assert data_entry["sensor_value"] == 42, "Sensor value should match the JSON file"
        assert "timestamp" in data_entry, "Data entry should contain a timestamp"
        # Optionally, ensure that the timestamp is a valid ISO 8601 string.
        timestamp_obj = datetime.fromisoformat(data_entry["timestamp"])
        assert isinstance(timestamp_obj, datetime), "Timestamp should be valid ISO 8601"

    def test_write_sensor_data(self, tmp_path):
        with patch("builtins.input", return_value="test_scent"):
            collector = SensorDataCollector(sensor_json_file="dummy_path")

        test_data = [
            {"sensor_value": 42, "timestamp": datetime.now().isoformat()},
            {"sensor_value": 43, "timestamp": datetime.now().isoformat()},
        ]
        collector.sensor_data_list = test_data.copy()

        output_file = tmp_path / "output.json"
        collector.write_sensor_data(str(output_file))

        with open(output_file, "r") as f:
            data_written = json.load(f)

        assert data_written == test_data


    def test_sensor_writer_thread(self, tmp_path):
        with patch("builtins.input", return_value="test_scent"):
            collector = SensorDataCollector(sensor_json_file="dummy_path", write_interval=1)
        output_file = tmp_path / "output.json"
        collector.write_sensor_data(str(output_file))

        writer_thread = collector.SensorWriterThread(collector, collector.output_file)

        collector.sensor_data_list.append({
            "sensor_value": 100,
            "timestamp": datetime.now().isoformat()
        })

        def stop_after():
            time.sleep(0.2)
            collector.stop_event.set()

        stopper_thread = threading.Thread(target=stop_after)
        stopper_thread.start()

        writer_thread.start()
        writer_thread.join()
        stopper_thread.join()
        
        with open(collector.output_file, "r") as f:
            data_written = json.load(f)
        assert isinstance(data_written, list) and len(data_written) >= 1

    def test_sensor_reader_thread(self, tmp_path):
        sensor_data_file = tmp_path / "sensor_data.json"
        sensor_data_file.write_text(json.dumps({"sensor_value": 55}))

        with patch("builtins.input", return_value="test_scent"):
            collector = SensorDataCollector(sensor_json_file=str(sensor_data_file), read_interval=1)
        
        reader_thread = collector.SensorReaderThread(collector)
        
        def stop_after():
            time.sleep(0.2)
            collector.stop_event.set()
        
        stopper_thread = threading.Thread(target=stop_after)
        stopper_thread.start()

        reader_thread.start()
        reader_thread.join()
        stopper_thread.join()

        assert len(collector.sensor_data_list) >= 1
