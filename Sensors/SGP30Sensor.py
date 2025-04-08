from Sensors.SensorInterface import Sensor 
import adafruit_sgp30

class SGP30Sensor(Sensor):
    def __init__(self, i2c):
        self.sensor = adafruit_sgp30.Adafruit_SGP30(i2c)
        self.sensor.set_iaq_baseline(0x8973, 0x8AAE)
        self.sensor.set_iaq_relative_humidity(celsius=22.1, relative_humidity=44)

    def read_data(self):
        return {
            "CO2": self.sensor.eCO2,
            "TVOC": self.sensor.TVOC
        }
