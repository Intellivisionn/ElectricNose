from Sensors.SensorInterface import Sensor 
import adafruit_sgp30

class SGP30Sensor(Sensor):
    def __init__(self, i2c):
        self.sensor = adafruit_sgp30.Adafruit_SGP30(i2c)
        self.sensor.iaq_init()
        self.sensor.set_iaq_relative_humidity(celsius=28, relative_humidity=28)

    def read_data(self):
        eco2, tvoc = self.sensor.iaq_measure()
        h2, ethanol = self.sensor.raw_measure()
        baseline = self.sensor.get_iaq_baseline()
        return {
                "CO2": eco2,
                "TVOC": tvoc,
                "BASELINE": baseline,
                "Raw H2": h2,
                "Raw Ethanol": ethanol
                }
