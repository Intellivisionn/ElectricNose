from SensorReader.Sensors.SensorInterface import Sensor

class BME680Sensor(Sensor):
    def __init__(self, loader):
        self.loader = loader

    def read_data(self):
        return self.loader.next()["BME680Sensor"]