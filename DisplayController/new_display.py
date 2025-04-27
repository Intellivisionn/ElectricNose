import time
from PIL import Image, ImageDraw
import Adafruit_GPIO.SPI as SPI

# ✅ Patch: force platform detection to Raspberry Pi
import Adafruit_GPIO.Platform as Platform
Platform.platform_detect = lambda: Platform.RASPBERRY_PI

import Adafruit_ILI9341 as TFT

# SPI config (adjust pins if needed)
DC = 24
RST = 25
SPI_PORT = 0
SPI_DEVICE = 0

# Initialize display
disp = TFT.ILI9341(DC, rst=RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=64000000))
disp.begin()

# Clear screen to black
disp.clear((0, 0, 0))

# Create an image and draw on it
image = Image.new('RGB', (disp.width, disp.height), (0, 0, 0))
draw = ImageDraw.Draw(image)
draw.rectangle((10, 10, 310, 230), outline=(255, 255, 255), fill=(0, 0, 255))
draw.text((20, 100), 'ILI9341 OK!', fill=(255, 255, 0))

# Show image on display
disp.display(image)

# Keep it visible
time.sleep(5)
disp.clear((0, 0, 0))