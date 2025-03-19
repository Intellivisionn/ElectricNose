import time
import json
from smbus2 import SMBus
import board
import adafruit_bme680
import adafruit_sgp30

bus = SMBus(1)

# Initialize BME680 Sensor
i2c = board.I2C()
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, address=0x76)

# Initialize SGP30 Sensor
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)
sgp30.iaq_init()

def read_sensor_data():
    """ Reads sensor data and returns it as a JSON-formatted dictionary. """
    data = {
        "BME680": {
            "Temperature": round(bme680.temperature, 2),
            "Humidity": round(bme680.humidity, 2),
            "Pressure": round(bme680.pressure, 2),
            "GasResistance": bme680.gas
        },
        "SGP30": {
            "CO2": sgp30.eCO2,
            "TVOC": sgp30.TVOC
        },
        "Grove": {register: bus.read_i2c_block_data(0x08, register, 2) for register in range(0x01, 0x09)}
    }
    return json.dumps(data, indent=4)

while True:
    sensor_json = read_sensor_data()
    #print(sensor_json)

    # Save JSON data to a file (can be read by another process)
    with open("/home/admin/ElectricNose-SensorReader/sensor_data.json", "w") as f:
        f.write(sensor_json)

    time.sleep(2)
