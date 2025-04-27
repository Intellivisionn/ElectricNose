from SensorReader.Sensors.SensorInterface import Sensor

class FakeSensor(Sensor):
    def read_data(self):
        print("Reading sensor data")
        return {"value": 42}

