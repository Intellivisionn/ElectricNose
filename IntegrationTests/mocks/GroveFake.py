from SensorReader.Sensors.SensorInterface import Sensor

class GroveGasSensor(Sensor):
    def __init__(self, loader):
        self.loader = loader

    def read_data(self):
        return self.loader.next()["GroveGasSensor"]
