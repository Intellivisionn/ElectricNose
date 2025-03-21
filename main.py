import time
import json
import board
from smbus2 import SMBus

# Import sensor classes
from Sensors.BME680Sensor import BME680Sensor
from Sensors.SGP30Sensor import SGP30Sensor
from Sensors.GroveGasSensor import GroveGasSensor
from Sensors.SensorManager import SensorManager

i2c = board.I2C()
bus = SMBus(1)

sensors = [
    BME680Sensor(i2c),
    SGP30Sensor(i2c),
    GroveGasSensor(bus)
]

manager = SensorManager(sensors)

while True:
    data = manager.read_all()
    sensor_json = json.dumps(data, indent=4)
    print(sensor_json)

    # Edit this in the future to have versatile output as well
    with open("/home/admin/ElectricNose-SensorReader/sensor_data.json", "w") as f:
        f.write(sensor_json)

    time.sleep(2)
