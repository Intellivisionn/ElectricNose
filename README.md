# ElectricNose-DisplayController

**ElectricNose-DisplayController** is a Python-based visualization tool designed to display real-time sensor readings from the Electric Nose system. It uses **Pygame** to show the data in fullscreen mode on an HDMI-connected screen, ideal for headless setups like Raspberry Pi.

## 📺 Features

- Displays real-time sensor data from `sensor_data.json`
- Fullscreen, auto-refreshing interface (every 5 seconds)
- Dynamically scales font sizes based on screen resolution
- Detects HDMI connection before starting the display
- Runs as a **systemd service** named `display`

## 🚀 Getting Started

### Prerequisites

- Raspberry Pi (or Linux system with HDMI)
- Python 3.x
- HDMI-connected display

### Installation

1. Clone the Repository:

```bash
git clone https://github.com/Intellivisionn/ElectricNose-DisplayController.git
cd ElectricNose-DisplayController
```

2. Install Dependencies:

```bash
sudo apt update
sudo apt install python3 python3-pygame libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
```

3. Create and Enable the systemd Service:

```bash
sudo cp display.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable display
sudo systemctl start display
```

4. Check If It’s Running:

```bash
sudo systemctl status display
```

5. Restart/Stop the Service:

```bash
sudo systemctl restart display
sudo systemctl stop display
```

## ⚙️ Configuration

- Modify `sensor_data.json` to provide your live sensor feed.
- Tweak fonts or layout in `hdmi_pygame.py` if needed.

## 🧪 Troubleshooting

- View logs to debug issues:

```bash
cat /var/log/display.log
```

- Reboot the system if necessary:

```bash
sudo reboot
```

## 🧠 Project Structure

```
ElectricNose-DisplayController/
├── hdmi_pygame.py        # Main display script
├── display.service       # Systemd service file
├── sensor_data.json      # Input source for sensor readings
└── README.md             # Project documentation
```

## 📜 License

This project is part of the Electric Nose system and is released under the MIT License. See `LICENSE` for details.

---

**Developed for the Electric Nose project — Spring Semester 2025**
