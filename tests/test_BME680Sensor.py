import pytest
from .BME_mock import FakeBME680Sensor  # Your actual sensor class

BME680Address = 0x76

@pytest.fixture
def mock_bme680_sensor():
    fake_sensor = FakeBME680Sensor()
    return fake_sensor


def test_bme680sensor_initialization(mock_bme680_sensor):
    assert isinstance(mock_bme680_sensor, FakeBME680Sensor)
    assert hasattr(mock_bme680_sensor, "temperature")
    assert hasattr(mock_bme680_sensor, "humidity")
    assert hasattr(mock_bme680_sensor, "pressure")
    assert hasattr(mock_bme680_sensor, "gas")

def test_bme680sensor_read_data(mock_bme680_sensor):
    data = mock_bme680_sensor.read_data()
    assert isinstance(data, dict)
    assert data == {
        "Temperature": 25.5,
        "Humidity": 50.2,
        "Pressure": 1013.25,
        "GasResistance": 120000
    }
