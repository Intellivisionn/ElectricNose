from Sensors.SensorInterface import Sensor 
import adafruit_bme680

BME680Address = 0x76


class BME680Sensor(Sensor):
    def __init__(self, i2c):
        self.sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c, BME680Address)

    def read_data(self):
        return {
            "Temperature": round(self.sensor.temperature, 2),
            "Humidity": round(self.sensor.humidity, 2),
            "Pressure": round(self.sensor.pressure, 2),
            "GasResistance": self.sensor.gas
        }
