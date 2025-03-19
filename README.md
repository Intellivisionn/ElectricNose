# Electric Nose Sensor Display

This script displays real-time sensor data from the Electric Nose system on an HDMI display using Pygame.
Later on will make to display the detected smell.

## Features
- Reads sensor data from `sensor_data.json`
- Displays data on an HDMI screen in fullscreen mode
- Auto-refreshes every 5 seconds
- Runs as a systemd service (`display`)

## Installation

### 1. Clone the Repository
```sh
git clone https://github.com/Intellivisionn/ElectricNose-DisplayController.git
cd ElectricNose-DisplayController
```

### 2. Install Dependencies
```sh
sudo apt update
sudo apt install python3 python3-pygame libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
```

### 3. Create and Enable the Service
```sh
sudo cp display.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable display
sudo systemctl start display
```

### 4. Check If It’s Running
```sh
sudo systemctl status display
```

### 5. Restart/Stop the Service
```sh
sudo systemctl restart display
sudo systemctl stop display
```

## Configuration
- Edit `sensor_data.json` to provide custom sensor data.
- Modify `hdmi_pygame.py` for layout or display tweaks.

## Troubleshooting
- Check logs if the display isn't working:
  ```sh
  cat /var/log/display.log
  ```
- Restart the system if needed:
  ```sh
  sudo reboot
  ```

## License
MIT License. See [LICENSE](LICENSE) for details.

