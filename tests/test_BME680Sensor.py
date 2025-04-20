from .BME_mock import FakeBME680Sensor  # Your actual sensor class
from Sensors.BME680Sensor import BME680Sensor

BME680Address = 0x76

class TestBME680Sensor:
    def test_bme680_sensor_read_data(self, mocker):
        mocker.patch('adafruit_bme680.Adafruit_BME680_I2C', FakeBME680Sensor)

        mock_i2c = mocker.Mock()
        sensor = BME680Sensor(mock_i2c)
        data = sensor.read_data()

        assert data == {
            "Temperature": 25.5,
            "Humidity": 50.2,
            "Pressure": 1013.25,
            "GasResistance": 120000
        }

