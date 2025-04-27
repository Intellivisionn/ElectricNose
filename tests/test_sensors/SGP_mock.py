from Sensors.SensorInterface import Sensor

class FakeSGP30Sensor(Sensor):
    def __init__(self, i2c=None):
        pass

    def iaq_init(self):
        pass  # Mock does nothing

    def set_iaq_baseline(self, eco2, tvoc):
        pass  # Mock does nothing

    def set_iaq_relative_humidity(self, celsius, relative_humidity):
        pass  # Mock does nothing

    def iaq_measure(self):
        return 400, 0.5

    def read_data(self):
        eco2, tvoc = self.iaq_measure()
        return {
            "CO2": eco2,
            "TVOC": tvoc,
        }
