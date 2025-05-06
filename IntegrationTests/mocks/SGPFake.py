from SensorReader.Sensors.SensorInterface import Sensor

class SGP30Sensor(Sensor):
    def __init__(self): pass

    def read_data(self):
        return {
            "TVOC": 120,
            "CO2": 400
        }
