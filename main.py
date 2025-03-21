import time
import json
import board
from smbus2 import SMBus

# Import sensor classes
from Sensors.BME680Sensor import BME680Sensor
from Sensors.SGP30Sensor import SGP30Sensor
from Sensors.GroveGasSensor import GroveGasSensor
from Sensors.SensorManager import SensorManager


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

    def read_and_save(self):
        while True:
            data = self.manager.read_all()
            sensor_json = json.dumps(data, indent=4)
            print(sensor_json)

            with open(self.output_path, "w") as f:
                f.write(sensor_json)

            time.sleep(self.sleep_interval)


if __name__ == "__main__":
    output_path = "/home/admin/ElectricNose-SensorReader/sensor_data.json"
    reader = ElectricNoseSensorReader(output_path)
    reader.read_and_save()
