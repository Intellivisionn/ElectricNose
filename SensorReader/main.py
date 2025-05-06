import time
import json
from pathlib import Path
from SensorReader.Sensors.SensorManager import SensorManager
from SensorReader.aspects.LoggingAspect import LoggingAspect
import board
from smbus2 import SMBus
from SensorReader.Sensors.BME680Sensor import BME680Sensor
from SensorReader.Sensors.SGP30Sensor import SGP30Sensor
from SensorReader.Sensors.GroveGasSensor import GroveGasSensor


class BaseSensorReader:
    def __init__(self, sensors, output_path, sleep_interval=2):
        self.sensors = sensors
        self.manager = SensorManager(self.sensors)
        self.output_path = output_path
        self.sleep_interval = sleep_interval

    @LoggingAspect.log_method
    def read_and_save(self):
        while True:
            self.read_and_save_once()
            time.sleep(self.sleep_interval)

    def read_and_save_once(self):
        data = self.manager.read_all()
        sensor_json = json.dumps(data, indent=4)
        with open(self.output_path, "w") as f:
            f.write(sensor_json)


class ElectricNoseSensorReader(BaseSensorReader):
    def __init__(self, output_path, sleep_interval=2):
        i2c = board.I2C()
        bus = SMBus(1)
        sensors = [
            BME680Sensor(i2c),
            SGP30Sensor(i2c),
            GroveGasSensor(bus)
        ]
        super().__init__(sensors, output_path, sleep_interval)

if __name__ == "__main__":
    output_path = Path(__file__).resolve().parent / "sensor_data.json"
    reader = ElectricNoseSensorReader(output_path)
    reader.read_and_save()