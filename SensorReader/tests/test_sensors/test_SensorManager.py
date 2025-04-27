import pytest

from .BME_mock import FakeBME680Sensor
from Sensors.BME680Sensor import BME680Sensor
from .SGP_mock import FakeSGP30Sensor
from Sensors.SGP30Sensor import SGP30Sensor
from Sensors.SensorManager import SensorManager

from .SensorWithoutInterface import SensorWithoutInterface


class TestSensorManager:
    def test_sensor_manager_read_all_fake_sensors(self, mocker):
        mocker.patch('adafruit_bme680.Adafruit_BME680_I2C', FakeBME680Sensor)
        mocker.patch('adafruit_sgp30.Adafruit_SGP30', FakeSGP30Sensor)

        mock_i2c = mocker.Mock()
        bme680 = BME680Sensor(mock_i2c)
        sgp30 = SGP30Sensor(mock_i2c)
        manager = SensorManager([bme680, sgp30])
        data = manager.read_all()

        assert "BME680Sensor" in data
        assert "SGP30Sensor" in data

        # Check BME680 data values
        bme_data = data["BME680Sensor"]
        assert bme_data["Temperature"] == 25.5
        assert bme_data["Humidity"] == 50.2
        assert bme_data["Pressure"] == 1013.25
        assert bme_data["GasResistance"] == 120000

        # Check SGP30 data values
        sgp_data = data["SGP30Sensor"]
        assert sgp_data["CO2"] == 400
        assert sgp_data["TVOC"] == 0.5


    def test_sensor_manager_read_all_no_sensors(self):
        manager = SensorManager([])  # No sensors
        data = manager.read_all()

        assert data == {}


    def test_sensor_manager_read_all_sensor_without_read_data_method(self, mocker):
        sensor = SensorWithoutInterface()
        manager = SensorManager([sensor])  # No sensors

        with pytest.raises(AttributeError):
            manager.read_all()


    def test_sensor_manager_read_all_duplicate_names(self, mocker):
        sensor1 = mocker.Mock()
        sensor1.__class__.__name__ = "SameSensor"
        sensor1.read_data.return_value = {"value": 1}

        sensor2 = mocker.Mock()
        sensor2.__class__.__name__ = "SameSensor"
        sensor2.read_data.return_value = {"value": 2}

        manager = SensorManager([sensor1, sensor2])
        data = manager.read_all()

        assert len(data) == 1
        assert data["SameSensor"]["value"] in (1, 2)

    def test_sensor_manager_read_all_value_none(self, mocker):
        bad_sensor = mocker.Mock()
        bad_sensor.__class__.__name__ = "BadSensor"
        bad_sensor.read_data.return_value = None

        manager = SensorManager([bad_sensor])
        data = manager.read_all()

        assert data["BadSensor"] is None


