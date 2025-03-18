import time
from smbus2 import SMBus
import board
import adafruit_bme680
import adafruit_sgp30

bus = SMBus(1)

# Initialize BME680 Sensor
i2c = board.I2C()
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, address=0x76)

# Initialize SGP30 Sensor
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)
sgp30.iaq_init()


while True:
    # Read BME680 Data
    temperature = bme680.temperature
    humidity = bme680.humidity
    pressure = bme680.pressure
    gas_resistance = bme680.gas

    # Read SGP30 Data
    co2_eq = sgp30.eCO2
    tvoc = sgp30.TVOC

    # Print Results
    print("\nBME680 Data:")
    print(f"  Temperature: {temperature:.2f} °C")
    print(f"  Humidity: {humidity:.2f} %")
    print(f"  Pressure: {pressure:.2f} hPa")
    print(f"  Gas Resistance: {gas_resistance} Ω")

    print("\nSGP30 Data:")
    print(f"  CO2: {co2_eq} ppm")
    print(f"  TVOC: {tvoc} ppb")

    print("\nGrove Data:")
    print(f"  NO2: {bus.read_i2c_block_data(0x08, 0x01, 2)}")
    print(f"  C2H5CH: {bus.read_i2c_block_data(0x08, 0x03, 2)}")
    print(f"  VOC: {bus.read_i2c_block_data(0x08, 0x05, 2)}")
    print(f"  CO: {bus.read_i2c_block_data(0x08, 0x07, 2)}")
    
    time.sleep(2)
