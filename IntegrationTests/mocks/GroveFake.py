from SensorReader.Sensors.SensorInterface import Sensor

class GroveGasSensor(Sensor):
    def __init__(self): pass

    def read_data(self):
        return {
            "NO2": 500,
            "Ethanol": 400,
            "VOC": 300,
            "CO": 200,
            "0x04": 600,
            "0x08": 600,
        }
