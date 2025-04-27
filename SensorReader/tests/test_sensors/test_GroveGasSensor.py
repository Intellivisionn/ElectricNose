import pytest
from SensorReader.Sensors.GroveGasSensor import GroveGasSensor

class TestGroveGasSensor:
    def test_write_byte(self, mocker):
        mock_bus = mocker.Mock()
        sensor = GroveGasSensor(mock_bus)

        sensor._write_byte(0x01)

        mock_bus.write_byte.assert_called_once_with(sensor.address, 0x01)


    def test_read_4_bytes(self, mocker):
        mocker.patch('SensorReader.Sensors.GroveGasSensor.WARMING_UP', 0xFE)
        mocker.patch('SensorReader.Sensors.GroveGasSensor.GM_102B', 0x01)
        mock_bus = mocker.Mock()
        mock_bus.read_i2c_block_data.return_value = [0x34, 0x12]  #  0x1234 → 4660

        sensor = GroveGasSensor(mock_bus)
        mocker.patch.object(sensor, '_write_byte')

        result = sensor._read_4_bytes(0x01)

        assert result == 4660
        sensor._write_byte.assert_any_call(0xFE)
        sensor._write_byte.assert_any_call(0x01)
        mock_bus.read_i2c_block_data.assert_called_once_with(sensor.address, 0x01, 2)


    def test_preheat_and_stop_preheat(self, mocker):
        mocker.patch('SensorReader.Sensors.GroveGasSensor.WARMING_UP', 0xFE)
        mocker.patch('SensorReader.Sensors.GroveGasSensor.WARMING_DOWN', 0xFF)
        mock_bus = mocker.Mock()
        sensor = GroveGasSensor(mock_bus)
        mocker.patch.object(sensor, '_write_byte')

        sensor.preheat()

        sensor._write_byte.assert_called_with(0xFE)
        assert sensor.is_preheated

        sensor.stop_preheat()

        sensor._write_byte.assert_called_with(0xFF)
        assert not sensor.is_preheated


    def test_change_address(self, mocker):
        mocker.patch('SensorReader.Sensors.GroveGasSensor.CHANGE_I2C_ADDR', 0x55)
        mock_bus = mocker.Mock()
        sensor = GroveGasSensor(mock_bus)

        sensor.change_address(0x10)
        mock_bus.write_i2c_block_data.assert_called_with(0x08, 0x55, [0x10])
        assert sensor.address == 0x10


    def test_change_address_invalid(self, mocker):
        mock_bus = mocker.Mock()
        sensor = GroveGasSensor(mock_bus)

        with pytest.raises(ValueError):
            sensor.change_address(0x01)


    def test_close(self, mocker):
        mock_bus = mocker.Mock()
        sensor = GroveGasSensor(mock_bus)

        sensor.close()
        mock_bus.close.assert_called_once()


    def test_read_data(self, mocker):
        sensor = GroveGasSensor(mocker.Mock())
        mocker.patch.object(sensor, 'measure_no2', return_value=10)
        mocker.patch.object(sensor, 'measure_ethanol', return_value=20)
        mocker.patch.object(sensor, 'measure_voc', return_value=30)
        mocker.patch.object(sensor, 'measure_co', return_value=40)
        mocker.patch.object(sensor, 'measure_4', return_value=50)
        mocker.patch.object(sensor, 'measure_8', return_value=60)

        result = sensor.read_data()

        assert result == {
            "NO2": 10,
            "Ethanol": 20,
            "VOC": 30,
            "CO": 40,
            "0x04": 50,
            "0x08": 60
        }


