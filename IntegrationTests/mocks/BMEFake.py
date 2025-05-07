from SensorReader.Sensors.SensorInterface import Sensor

class BME680Sensor(Sensor):
    def __init__(self): pass

    def read_data(self):
        return {
            "Temperature": 22.5,
            "Humidity": 50.1,
            "Pressure": 1008.2,
            "GasResistance": 14000
        }
