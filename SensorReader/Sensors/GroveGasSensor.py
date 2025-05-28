import time
from SensorReader.Sensors.SensorInterface import Sensor

# Default I2C Address for GMXXX sensor
DEFAULT_I2C_ADDRESS = 0x08

# Sensor Commands
GM_102B = 0x01  # NO2
GM_302B = 0x03  # Ethanol (C2H5OH)
GM_502B = 0x05  # VOC
GM_702B = 0x07  # CO
GM_4 = 0x04
GM_8 = 0x08
CHANGE_I2C_ADDR = 0x55
WARMING_UP = 0xFE
WARMING_DOWN = 0xFF

class GroveGasSensor(Sensor):
    def __init__(self, i2c_bus, address=DEFAULT_I2C_ADDRESS):
        self.bus = i2c_bus
        self.address = address
        self.is_preheated = False

    def read_data(self):
        return {
            "NO2": self.measure_no2(),
            "Ethanol": self.measure_ethanol(),
            "VOC": self.measure_voc(),
            "CO": self.measure_co(),
            "0x04": self.measure_4(),
            "0x08": self.measure_8(),
        }
    
    def _write_byte(self, command):
        """ Send a single command byte over I2C. """
        #print(f"Writing command {hex(command)} to I2C address {hex(self.address)}")
        self.bus.write_byte(self.address, command)
        time.sleep(0.01)
    
    def _read_4_bytes(self, command):
        #if not self.is_preheated:
        #    self.preheat()
        self._write_byte(WARMING_UP)
        self._write_byte(command)
        time.sleep(0.05)  # Allow time for sensor to respond
        data = self.bus.read_i2c_block_data(self.address, command, 2) #library adviced 4, but when you run it with 2 it is the same actually
        value = int.from_bytes(data, byteorder='little')
        #print(f"Read {value} from command {hex(command)}")
        return value
    
    def preheat(self):
        """ Warm up the sensor (equivalent to C++ preheated). """
        self._write_byte(WARMING_UP)
        self.is_preheated = True
        time.sleep(0.1)

    def stop_preheat(self):
        """ Stop sensor warm-up (equivalent to C++ unPreheated). """
        self._write_byte(WARMING_DOWN)
        self.is_preheated = False
        time.sleep(0.1)

    def measure_no2(self):
        """ Measure NO2 gas concentration. """
        return self._read_4_bytes(GM_102B)
    
    def measure_ethanol(self):
        """ Measure Ethanol (C2H5OH) gas concentration. """
        return self._read_4_bytes(GM_302B)
    
    def measure_voc(self):
        """ Measure VOC gas concentration. """
        return self._read_4_bytes(GM_502B)
    
    def measure_co(self):
        """ Measure CO gas concentration. """
        return self._read_4_bytes(GM_702B)
    
    def measure_4(self):
        return self._read_4_bytes(GM_4)
    
    def measure_8(self):
        return self._read_4_bytes(GM_8)
    
    def change_address(self, new_address):
        """ Change the I2C address of the sensor. """
        if new_address < 0x08 or new_address > 0x7F:
            raise ValueError("Invalid I2C address. Must be between 0x08 and 0x7F.")
        #print(f"Changing I2C address to {hex(new_address)}")
        self.bus.write_i2c_block_data(self.address, CHANGE_I2C_ADDR, [new_address])
        self.address = new_address
        time.sleep(0.1)

    def close(self):
        """ Close the I2C connection. """
        #print("Closing I2C connection.")
        self.bus.close()
"""
if __name__ == "__main__":
    sensor = GroveGasSensor()
    i = 0
    while True:
        print(f"----------[Repetition: {i}]-----------")
        i += 1
        print("NO2 Level:", sensor.measure_no2())
        print("Ethanol Level:", sensor.measure_ethanol())
        print("VOC Level:", sensor.measure_voc())
        print("CO Level:", sensor.measure_co())
        print("0x04: ", sensor.measure_4())
        print("0x08: ", sensor.measure_8())
        print("--------------------------------------")
        time.sleep(2)
"""
