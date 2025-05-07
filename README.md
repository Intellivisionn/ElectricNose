# ElectricNose System

The **ElectricNose** project is a full-stack sensing system designed to collect, process, and visualize environmental data in real-time, developed as a semester project in Spring 2025.

It consists of three main components:

- **SensorReader** – Real-time sensor data collection
- **DisplayController** – Live visualization on HDMI/Adafruit screens
- **DataReader** – Historical data logging for analysis

---

## 📦 Repository Structure

```
ElectricNose/
├── SensorReader/                # Sensor data collection module
├── DisplayController/           # Real-time visualization module
├── DataReader/                  # Data logging module
├── services/                    # systemd service files
├── README.md                    # (this file)
├── LICENSE                      # MIT License
└── .github/workflows/           # CI pipelines
```

---

## 🚀 Components Overview

### 📈 SensorReader

Python module that continuously collects environmental readings from various sensors and outputs them to a shared `sensor_data.json`.

- Modular sensor classes (BME680, SGP30, Grove)
- Python `venv/` isolation
- systemd service: `sensor.service`
- Automatic logging and update support

**Start manually:**

```bash
cd SensorReader
source venv/bin/activate
python3 main.py
```

**Run as a service:**

```bash
sudo cp services/sensor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sensor.service
sudo systemctl start sensor.service
```

---

### 🎥 DisplayController

Pygame-based fullscreen visualization of live sensor data, designed for HDMI-connected or PiTFT displays.

- Dynamically scaled fonts
- HDMI/Small screen toggle
- systemd service: `display.service`
- JSON payload socket API for custom messages

**Start manually:**

```bash
cd DisplayController
python3 hdmi_pygame.py
```

**Run as a service:**

```bash
sudo cp services/display.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable display.service
sudo systemctl start display.service
```

---

### 💃 DataReader

Background process that reads sensor data every few seconds and archives it with timestamps.

- Threaded reader/writer design
- Customizable intervals
- Saves output JSON files per scent capture session

**Start manually:**

```bash
cd DataReader
python3 main.py
```

You'll be prompted for a "scent" name, and a file like `mint_20250420_152010.json` will be saved inside `DataReader/savedData/`.

---

## ⚙️ Installation & Setup

### Prerequisites

- Raspberry Pi 4 / Linux system
- Python 3.7+
- HDMI or small TFT screen
- Basic Linux terminal knowledge

### Install Dependencies (System-wide)

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv python3-pygame libsdl2-dev libsdl2-ttf-dev
```

---

## 🧪 Running Services

To enable and manage systemd services:

```bash
# Copy service files
sudo cp services/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable sensor.service
sudo systemctl enable display.service
sudo systemctl start sensor.service
sudo systemctl start display.service
```

---

## 🔥 Usage Tips

- **Sensor data JSON:**  
  `/home/admin/ElectricNose/SensorReader/sensor_data.json`

- **Service Logs:**  
  Check logs via:

  ```bash
  sudo journalctl -u sensor.service
  sudo journalctl -u display.service
  ```

- **Manually monitor logs:**

  ```bash
  tail -f /path/to/your/logfile.log
  ```

- **Restart services after updates:**

  ```bash
  sudo systemctl restart sensor.service
  sudo systemctl restart display.service
  ```

---

## 🧐 Sensor Data Example

Example sensor data stored and visualized:

```json
[
  {
    "BME680": {
      "Temperature": 22.5,
      "Humidity": 45.2,
      "Pressure": 1013.2,
      "GasResistance": 12000
    },
    "SGP30": {
      "CO2": 400,
      "TVOC": 10
    },
    "Grove": {
      "Gas": 350
    }
  }
]
```

---

## 🧹 Maintenance

- Update code via:

  ```bash
  git pull
  ```

- Reinstall Python packages if needed:

  ```bash
  source venv/bin/activate
  pip install -r requirements.txt
  ```

---

## 📜 License

This project is licensed under the **MIT License**.

See the [LICENSE](./LICENSE) file for details.

---

**Developed for the Electric Nose Project — 4th Semester, Spring 2025.**