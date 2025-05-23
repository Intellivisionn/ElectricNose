# Display Controller Setup

## Hardware Requirements
- Raspberry Pi (tested on Pi 4)
- ILI9341 Display
- Proper display connections via SPI

## Initial Setup

### 1. System Dependencies
```bash
# Update system
sudo apt-get update
sudo apt-get upgrade

# Install required packages
sudo apt-get install -y \
    python3 \
    python3-pip \
    libsdl2-dev \
    libsdl2-2.0-0 \
    python3-pygame

### Display Drivers Setup
# Add user to required groups
sudo usermod -a -G video,input,spi,gpio $USER

# Set permissions for display devices
sudo chmod 666 /dev/fb0
sudo chmod 666 /dev/dri/card1

###Advanced Chat AssistantAnthropic - Claude 3.5 Sonnet

# Display Controller Setup

## Hardware Requirements
- Raspberry Pi (tested on Pi 4)
- ILI9341 Display
- Proper display connections via SPI

## Initial Setup

### 1. System Dependencies
```bash
# Update system
sudo apt-get update
sudo apt-get upgrade

# Install required packages
sudo apt-get install -y \
    python3 \
    python3-pip \
    libsdl2-dev \
    libsdl2-2.0-0 \
    python3-pygame

2. Display Driver Setup

# Add user to required groups
sudo usermod -a -G video,input,spi,gpio $USER

# Set permissions for display devices
sudo chmod 666 /dev/fb0
sudo chmod 666 /dev/dri/card1

3. Configure Boot Settings

Edit /boot/firmware/config.txt:
```
sudo nano /boot/firmware/config.txt
```

Add under [all] section:
```
dtoverlay=pitft28-capacitive,rotate=90,speed=64000000,fps=30
dtoverlay=vc4-kms-v3d
gpu_mem=128
```

### # Clone repository (if not already done)
git clone <repository-url>
cd ElectricNose

# Set up service
sudo cp system-services/display.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable display
sudo systemctl start display
>>>>>>> main
