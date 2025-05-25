from SensorReader.Sensors.SensorInterface import Sensor

class SGP30Sensor(Sensor):
    def __init__(self, loader):
        self.loader = loader

    def read_data(self):
        return self.loader.next()["SGP30Sensor"]