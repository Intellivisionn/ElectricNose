import time
import smbus2

# Default I2C Address for GMXXX sensor
DEFAULT_I2C_ADDRESS = 0x08

# Sensor Commands
GM_102B = 0x01  # NO2
GM_302B = 0x03  # Ethanol (C2H5OH)
GM_502B = 0x05  # VOC
GM_702B = 0x07  # CO
CHANGE_I2C_ADDR = 0x55
WARMING_UP = 0xFE
WARMING_DOWN = 0xFF

class GroveGasSensor:
    def __init__(self, i2c_bus=1, address=DEFAULT_I2C_ADDRESS):
        self.bus = smbus2.SMBus(i2c_bus)
        self.address = address
        self.is_preheated = False
        self.preheat()

    def preheat(self):
        """ Warm up the sensor before reading. """
        self._write_byte(WARMING_UP)
        self.is_preheated = True
        time.sleep(1)
    
    def unpreheat(self):
        """ Turn off the preheat mode. """
        self._write_byte(WARMING_DOWN)
        self.is_preheated = False
    
    def _write_byte(self, command):
        """ Send a single command byte over I2C. """
        self.bus.write_byte(self.address, command)
        time.sleep(0.01)
    
    def _read_4_bytes(self):
        """ Read 4 bytes of data from the sensor. """
        data = self.bus.read_i2c_block_data(self.address, 0, 4)
        return int.from_bytes(data, byteorder='little')
    
    def measure_no2(self):
        """ Measure NO2 gas concentration. """
        return self._measure_gas(GM_102B)
    
    def measure_ethanol(self):
        """ Measure Ethanol (C2H5OH) gas concentration. """
        return self._measure_gas(GM_302B)
    
    def measure_voc(self):
        """ Measure VOC gas concentration. """
        return self._measure_gas(GM_502B)
    
    def measure_co(self):
        """ Measure CO gas concentration. """
        return self._measure_gas(GM_702B)
    
    def _measure_gas(self, command):
        """ Generic gas measurement function. """
        if not self.is_preheated:
            self.preheat()
        self._write_byte(command)
        return self._read_4_bytes()
    
    def change_address(self, new_address):
        """ Change the I2C address of the sensor. """
        if new_address < 0x08 or new_address > 0x7F:
            raise ValueError("Invalid I2C address. Must be between 0x08 and 0x7F.")
        self.bus.write_i2c_block_data(self.address, CHANGE_I2C_ADDR, [new_address])
        self.address = new_address
        time.sleep(0.1)

    def close(self):
        """ Close the I2C connection. """
        self.bus.close()

if __name__ == "__main__":
    sensor = GroveGasSensor()
    print("NO2 Level:", sensor.measure_no2())
    print("Ethanol Level:", sensor.measure_ethanol())
    print("VOC Level:", sensor.measure_voc())
    print("CO Level:", sensor.measure_co())
    sensor.close()
