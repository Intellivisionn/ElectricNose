from Sensors.SensorInterface import Sensor 
import adafruit_sgp30

class SGP30Sensor(Sensor):
    def __init__(self, i2c):
        self.sensor = adafruit_sgp30.Adafruit_SGP30(i2c)
        self.sensor.iaq_init()
        self.sensor.set_iaq_baseline(0x8973, 0x8AAE)
        self.sensor.set_iaq_relative_humidity(celsius=22.1, relative_humidity=44)

    def read_data(self):
        eco2, tvoc = self.sensor.iaq_measure()
        return {
            "CO2": eco2,
            "TVOC": tvoc
        }
