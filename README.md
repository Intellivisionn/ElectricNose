# ElectricNose System

The **ElectricNose** project is a sensing system designed to collect, process, and visualize environmental data in real-time, developed as a semester project in Spring 2025.

It consists of these components:

- **SensorReader** – Real-time sensor data collection
- **DisplayController** – Live visualization and IO Controlls
- **DataCollector** – Historical data logging from Sensors for training the model
- **DataCommunicator** - Allows communication between different components
- **OdourRecognizer** - The ML module making the odour classification possible.
- **GraphPlotter** - Plot graphs using the collected sensor information.
- **ModelTraining** - Traing the ML module for OdourRecognition improvements

---

## 📦 Repository Structure

```
ElectricNose/
├── SensorReader/                # Sensor data collection module
├── DisplayController/           # Real-time visualization module
├── DataCollector/               # Data logging module
├── DataCommunicator/            # Communication beacon
├── GraphPlotter/                # Plotting graphs to understand data
├── ModelTraining/               # Train the ML model
├── IntegrationTests/            # Robot Framework integration test for system modules
├── system-services/             # systemd service files
├── README.md                    # (this file)
├── .gitignore                   # Files to be ignored by GitHub
├── .gitmodules                  # Git sub-repositories used by project
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
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

---

### 🎥 DisplayController

Pygame-based fullscreen Real-time visualization + IO component, designed for PiTFT display.

- Dynamically scaled fonts
- HDMI/PiTFT screen toggle
- systemd service: `display.service`
- JSON payload socket API for custom messages

**Start manually:**

```bash
cd DisplayController/
source venv/bin/activate
sudo python adafruit-pitft.py --display=28r --rotation=270 --install-type=console

#check devices:
ls -l /dev/fb*
ls -l /dev/dri/*
dmesg | grep -i 'drm\|vc4'

#dont forget to:
sudo chmod 666 /dev/dri/card2
sudo chmod 666 /dev/dri/renderD128

python display/display_main.py
```

In a different terminal:
```bash
cd DisplayController/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python io/io_main.py
```

---

### 💃 DataCollector

Process that reads sensor data every few seconds and archives it with timestamps.

- Threaded reader/writer design
- Customizable intervals
- Saves output JSON files per scent capture session

**Use it:**

```bash
cd DataCollector
python -m venv venv
source /venv/bin/activate
pip install -r requirements.txt
python source/data_collector.py
```

You'll be prompted for a "scent" name, and a file like `mint_20250420_152010.json` will be saved inside `DataCollector/savedData/` (can differ according to the selected method in the Manager class)

---

### 🔗 DataCommunicator

The **DataCommunicator** is a lightweight, asynchronous WebSocket-based messaging layer that enables decoupled communication between all system modules (SensorReader, DisplayController, DataCollector, etc.).

It uses a **publish-subscribe model**:
- Clients can **send** to topics or their client name (e.g., `"topic:sensor_readings"`)
- Other clients **subscribe** to receive those messages
- A central **MessageBrokerServer** routes messages and handles registration

**Features:**
- Asynchronous WebSocket message broker
- Topic-based publish/subscribe messaging
- Broadcast support
- Easily extendable with custom clients
- Thread-safe integration into long-running UI or hardware loops

**Available topics:**
- `topic:sensor` – Data emitted from `SensorReader`, consumed by DataCollector, OdourRecognizer, etc.
- `topic:states` – Published by `IOHandler`, consumed by `DisplayController`, `OdourRecognizer`, etc.

**Example Pub/Sub Flow:**
```
SensorReader → topic:sensor → DataCollector
IOHandler → topic:states → DisplayController, OdourRecognizer
```

**Run the message broker:**
```bash
cd DataCommunicator
python -m venv venv
source /venv/bin/activate
pip install -r requirements.txt
python MessageBrokerServer.py
```

**Client Example:**
```python
await self.connection.send('topic:sensor_readings', payload)
await self.connection.subscribe('sensor_readings')
```

## ⚙️ Installation & Setup

### Prerequisites

- Raspberry Pi 4 / Linux system
- Python 3.7+
- small TFT screen
- Basic Linux terminal knowledge

### Install Dependencies (System-wide)

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv libsdl2-dev libsdl2-ttf-dev
```

---

## 🧪 Running Services

To enable and manage systemd services:

```bash
# Copy service files
sudo cp services/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable communicator.service
sudo systemctl enable sensor.service
sudo systemctl enable display.service
sudo systemctl enable io.service
sudo systemctl enable recognizer.service

sudo systemctl start communicator.service
sudo systemctl start sensor.service
sudo systemctl start display.service
sudo systemctl start io.service
sudo systemctl start recognizer.service
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

Example sensor data:

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
