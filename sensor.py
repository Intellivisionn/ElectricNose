import time
import json
import smbus2

# Default I2C Address for GMXXX sensor
DEFAULT_I2C_ADDRESS = 0x08

# Sensor Commands
GM_102B = 0x01  # NO2
GM_302B = 0x03  # Ethanol (C2H5OH)
GM_402B = 0x04  # (Potential NH3 or other gas)
GM_502B = 0x05  # VOC
GM_702B = 0x07  # CO
GM_802B = 0x08  # (Potential additional VOC/CO detection)
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
        time.sleep(5)  # Increased preheat time
    
    def unpreheat(self):
        """ Turn off the preheat mode. """
        self._write_byte(WARMING_DOWN)
        self.is_preheated = False
    
    def _write_byte(self, command):
        """ Send a single command byte over I2C. """
        self.bus.write_byte(self.address, command)
        time.sleep(0.01)
    
    def _read_2_bytes(self, register):
        """ Read 2 bytes of data from the sensor for compatibility with existing working code. """
        return self.bus.read_i2c_block_data(self.address, register, 2)
    
    def read_all_sensors(self):
        """ Reads all Grove sensor registers (0x01 to 0x08) and returns a dictionary. """
        return {register: self._read_2_bytes(register) for register in range(0x01, 0x09)}
    
    def measure_gm402b(self):
        """ Measure possible NH3 or another gas concentration. """
        return self._read_2_bytes(GM_402B)
    
    def measure_gm802b(self):
        """ Measure possible additional VOC or CO detection. """
        return self._read_2_bytes(GM_802B)
    
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
    print("Grove Sensor Data:", sensor.read_all_sensors())
    print("GM402B Measurement:", sensor.measure_gm402b())
    print("GM802B Measurement:", sensor.measure_gm802b())
    sensor.close()