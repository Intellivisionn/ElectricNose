from .SGP_mock import FakeSGP30Sensor  # Your actual sensor class
from Sensors.SGP30Sensor import SGP30Sensor

BME680Address = 0x76
class TestSGP30Sensor:
    def test_sgp30_sensor_read_data(self, mocker):
        mocker.patch('adafruit_sgp30.Adafruit_SGP30', FakeSGP30Sensor)

        mock_i2c = mocker.Mock()
        sensor = SGP30Sensor(mock_i2c)
        data = sensor.read_data()

        assert data == {
            "CO2": 400,
            "TVOC": 0.5
        }

