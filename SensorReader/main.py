import time
import json
import board
from smbus2 import SMBus
from pathlib import Path

# Import sensor classes
from SensorReader.Sensors.BME680Sensor import BME680Sensor
from SensorReader.Sensors.SGP30Sensor import SGP30Sensor
from SensorReader.Sensors.GroveGasSensor import GroveGasSensor
from SensorReader.Sensors.SensorManager import SensorManager
from SensorReader.aspects.LoggingAspect import LoggingAspect


class ElectricNoseSensorReader:
    def __init__(self, output_path, sleep_interval=2):
        self.i2c = board.I2C()
        self.bus = SMBus(1)
        self.sensors = [
            BME680Sensor(self.i2c),
            SGP30Sensor(self.i2c),
            GroveGasSensor(self.bus)
        ]
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
        #            print(sensor_json)

        with open(self.output_path, "w") as f:
            f.write(sensor_json)


if __name__ == "__main__":
    output_path = Path.cwd() / "sensor_data.json"
    reader = ElectricNoseSensorReader(output_path)
    reader.read_and_save()
