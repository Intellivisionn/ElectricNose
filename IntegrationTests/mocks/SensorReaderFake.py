import time
import json
from pathlib import Path

# Import sensor classes
from BMEFake import BME680Sensor
from SGPFake import SGP30Sensor
from GroveFake import GroveGasSensor
from SensorReader.Sensors.SensorManager import SensorManager
from SensorReader.aspects.LoggingAspect import LoggingAspect
from SensorReader.main import BaseSensorReader

class FakeElectricNoseSensorReader(BaseSensorReader):
    def __init__(self, output_path, sleep_interval=2):
        sensors = [
            BME680Sensor(),
            SGP30Sensor(),
            GroveGasSensor()
        ]
        super().__init__(sensors, output_path, sleep_interval)

if __name__ == "__main__":
    output_path = Path.cwd() / "sensor_data.json"
    reader = FakeElectricNoseSensorReader(output_path)
    reader.read_and_save()