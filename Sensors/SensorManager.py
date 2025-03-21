class SensorManager:
    def __init__(self, sensors):
        self.sensors = sensors

    def read_all(self):
        data = {}
        for sensor in self.sensors:
            sensor_name = sensor.__class__.__name__
            data[sensor_name] = sensor.read_data()
        return data
