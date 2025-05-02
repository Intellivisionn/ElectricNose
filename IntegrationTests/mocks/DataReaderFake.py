from DataReader.source.data_reader import SensorDataCollector
from pathlib import Path

if __name__ == "__main__":
    # Specify the path to the JSON file containing sensor data
    sensor_json_file = Path(__file__).resolve().parent / "sensor_data.json"
    output_dir = Path(__file__).resolve().parent / "savedData"
    
    # Create an instance of the SensorDataCollector
    collector = SensorDataCollector(sensor_json_file, read_interval=2, write_interval=5, output_dir=output_dir)
    
    # Start collecting and writing data
    collector.start()