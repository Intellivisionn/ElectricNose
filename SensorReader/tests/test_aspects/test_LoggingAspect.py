from .FakeSensor import FakeSensor
from SensorReader.Sensors.SensorManager import SensorManager

# mock hardware to use ElectricNoseSensorReader
import sys
from unittest.mock import MagicMock
sys.modules['smbus2'] = MagicMock()

from main import ElectricNoseSensorReader


class TestLoggingAspect:
    # test naming == test + {module/package} + {class/fileName} + {function/method} + {case}

    # capfd is a pytest fixture for capturing output
    def test_logging_aspect_sensor_interface_subclasses_read_data(self, capfd):
        sensor = FakeSensor()

        sensor.read_data()

        out, err = capfd.readouterr()
        lines = out.strip().splitlines()

        expected_lines = [
            "[LOG] Before calling FakeSensor.read_data()",
            "Reading sensor data",
            "[LOG] After calling FakeSensor.read_data()",
        ]

        assert expected_lines == lines[:len(expected_lines)]


    def test_logging_aspect_sensor_manager_read_all_without_sensors(self, capfd):
        # no sensors
        manager = SensorManager([])

        manager.read_all()

        out, err = capfd.readouterr()

        lines = out.strip().splitlines()

        expected_lines = [
            "[LOG] Before calling SensorManager.read_all()",
            "[LOG] After calling SensorManager.read_all()"
        ]

        assert expected_lines == lines[:len(expected_lines)]


    def test_logging_aspect_sensor_manager_read_all_with_sensor(self, capfd):
        # one sensor
        sensor = FakeSensor()
        manager = SensorManager([sensor])

        manager.read_all()

        out, err = capfd.readouterr()

        lines = out.strip().splitlines()

        expected_lines = [
            "[LOG] Before calling SensorManager.read_all()",
            "[LOG] Before calling FakeSensor.read_data()",
            "Reading sensor data",
            "[LOG] After calling FakeSensor.read_data()",
            "[LOG] After calling SensorManager.read_all()"
        ]

        assert expected_lines == lines[:len(expected_lines)]

    def test_logging_aspect_sensor_manager_read_all_with_multiple_sensors(self, capfd):
        # multiple sensors
        sensor1 = FakeSensor()
        sensor2 = FakeSensor()
        manager = SensorManager([sensor1, sensor2])

        manager.read_all()

        out, err = capfd.readouterr()

        lines = out.strip().splitlines()

        expected_lines = [
            "[LOG] Before calling SensorManager.read_all()",
            "[LOG] Before calling FakeSensor.read_data()",
            "Reading sensor data",
            "[LOG] After calling FakeSensor.read_data()",
            "[LOG] Before calling FakeSensor.read_data()",
            "Reading sensor data",
            "[LOG] After calling FakeSensor.read_data()",
            "[LOG] After calling SensorManager.read_all()"
        ]

        assert expected_lines == lines[:len(expected_lines)]


    def test_logging_aspect_electronic_nose_sensor_reader_read_and_save(self, capfd, mocker):
        mocker.patch("main.ElectricNoseSensorReader.__init__", return_value=None)
        electronic_nose_sensor_reader = ElectricNoseSensorReader("mock_output.json", sleep_interval=0)

        electronic_nose_sensor_reader.manager = mocker.Mock()
        electronic_nose_sensor_reader.output_path = "mock_output.json"
        electronic_nose_sensor_reader.sleep_interval = 0

        # assigning a side_effect to a mocked method ==> 1. call = returns {"value": 42} , 2. call raises a KeyboardInterrupt exception
        electronic_nose_sensor_reader.manager.read_all.side_effect = [{"value": 42}, KeyboardInterrupt]

        # fake file
        mocker.patch("builtins.open", mocker.mock_open())
        # fake sleep time
        mocker.patch("time.sleep")

        try:
            electronic_nose_sensor_reader.read_and_save()
        except KeyboardInterrupt:
            pass

        out, err = capfd.readouterr()

        lines = out.strip().splitlines()

        expected_lines = [
            "[LOG] Before calling ElectricNoseSensorReader.read_and_save()",
            "[LOG] After calling ElectricNoseSensorReader.read_and_save()"
        ]

        assert expected_lines == lines[:len(expected_lines)]




