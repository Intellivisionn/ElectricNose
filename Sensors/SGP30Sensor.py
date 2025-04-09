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
	h2, ethanol = self.sensor.raw_measure()
	eco2_base, tvoc_base = self.sensor.get_iaq_baseline()
        return {
            "CO2": eco2,
            "TVOC": tvoc,
	    "BASELINE CO2": eco2_base,
	    "BASELINE TVOC": tvoc_base,
	    "Raw H2": h2,
	    "Raw Ethanol": ethanol
        }
