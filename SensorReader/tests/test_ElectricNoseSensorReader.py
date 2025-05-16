import sys
from unittest.mock import MagicMock

import pytest

sys.modules['DataCommunicator.source.WebSocketConnection'] = MagicMock()
sys.modules['DataCommunicator.source.BaseDataClient']    = MagicMock()
sys.modules['smbus2'] = MagicMock()
from SensorReader.main import ElectricNoseSensorReader


class TestElectricNoseSensorReader:
    @pytest.fixture(autouse=True)
    def mock_hardware(self, mocker):
        mocker.patch("SensorReader.main.board", return_value="mocked_i2c")
        mocker.patch("SensorReader.main.SMBus", return_value="mocked_bus")
        mocker.patch("SensorReader.main.BME680Sensor", return_value=MagicMock())
        mocker.patch("SensorReader.main.SGP30Sensor", return_value=MagicMock())
        mocker.patch("SensorReader.main.GroveGasSensor", return_value=MagicMock())

    def test_electric_nose_sensor_reader_read_and_save_once(self, mocker):
        output_path = "fake_output.json"
        sensor_reader = ElectricNoseSensorReader(output_path)

        mocker.patch.object(sensor_reader.manager, 'read_all', return_value={

            "BME680Sensor": {
                "Temperature": 27.98,
                "Humidity": 37.8,
                "Pressure": 1022.02,
                "GasResistance": 68894
            },
            "SGP30Sensor": {
                "CO2": 400,
                "TVOC": 0
            },
            "GroveGasSensor": {
                "NO2": 397,
                "Ethanol": 491,
                "VOC": 323,
                "CO": 322,
                "0x04": 635,
                "0x08": 678
            },
            "timestamp": "2025-04-25T17:50:11.944292"

        })

        mock_open = mocker.patch("SensorReader.main.open", mocker.mock_open())

        sensor_reader.read_and_save_once()

        handle = mock_open()
        written_content = handle.write.call_args[0][0]
        lines = written_content.strip().splitlines()

        expected_lines = [
            '{',
            '    "BME680Sensor": {',
            '        "Temperature": 27.98,',
            '        "Humidity": 37.8,',
            '        "Pressure": 1022.02,',
            '        "GasResistance": 68894',
            '    },',
            '    "SGP30Sensor": {',
            '        "CO2": 400,',
            '        "TVOC": 0',
            '    },',
            '    "GroveGasSensor": {',
            '        "NO2": 397,',
            '        "Ethanol": 491,',
            '        "VOC": 323,',
            '        "CO": 322,',
            '        "0x04": 635,',
            '        "0x08": 678',
            '    },',
            '    "timestamp": "2025-04-25T17:50:11.944292"',
            '}'
        ]

        assert expected_lines == lines[:len(expected_lines)]


    def test_electric_nose_sensor_reader_read_and_save_once_empty_read_all(self, mocker):
        output_path = "fake_output.json"
        sensor_reader = ElectricNoseSensorReader(output_path)

        mocker.patch.object(sensor_reader.manager, 'read_all', return_value={})

        mock_open = mocker.patch("SensorReader.main.open", mocker.mock_open())

        sensor_reader.read_and_save_once()

        handle = mock_open()
        written_content = handle.write.call_args[0][0]
        lines = written_content.strip().splitlines()

        expected_lines = [
            '{}'
        ]

        assert expected_lines == lines[:len(expected_lines)]


    def test_electric_nose_sensor_reader_read_and_save_once_open_was_called(self, mocker):
        output_path = "fake_output.json"
        sensor_reader = ElectricNoseSensorReader(output_path)

        mocker.patch.object(sensor_reader.manager, 'read_all', return_value={})

        mock_open = mocker.patch("SensorReader.main.open", mocker.mock_open())

        sensor_reader.read_and_save_once()

        mock_open.assert_called_once_with(output_path, "w")
