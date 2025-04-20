from Sensors.SensorInterface import Sensor

class FakeBME680Sensor(Sensor):
    def __init__(self):
        self.temperature = 25.5
        self.humidity = 50.2
        self.pressure = 1013.25
        self.gas = 120000

    def read_data(self):
        return {
            "Temperature": self.temperature,
            "Humidity": self.humidity,
            "Pressure": self.pressure,
            "GasResistance": self.gas
        }
