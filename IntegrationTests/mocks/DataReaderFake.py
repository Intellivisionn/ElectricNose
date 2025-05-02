from DataReader.source.data_reader import SensorDataCollector

if __name__ == "__main__":
    # Specify the path to the JSON file containing sensor data
    sensor_json_file = "/home/IntegrationTests/mocks/sensor_data.json"
    
    # Create an instance of the SensorDataCollector
    collector = SensorDataCollector(sensor_json_file, read_interval=2, write_interval=5, output_dir="/home/admin/ElectricNose/IntegrationTests/savedData")
    
    # Start collecting and writing data
    collector.start()