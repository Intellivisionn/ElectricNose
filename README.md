# ElectricNose-SensorReader

**ElectricNose-SensorReader** is the data acquisition module of the Electric Nose system. It continuously collects readings from multiple I2C and analog sensors and writes the results to a JSON file for downstream consumption and visualization.

## 🔧 Features

- Component-based sensor architecture using `SensorManager`
- Reads from BME680, SGP30, and Grove gas sensors
- Outputs real-time sensor data to `sensor_data.json`
- Runs as a systemd service on boot
- Isolated environment via Python virtual environment (`venv/`)
- Auto-update support with logging

## 📁 Project Structure

```
ElectricNose-SensorReader/
├── Sensors/               # Modular sensor classes (BME680, SGP30, Grove)
├── venv/                  # Python virtual environment (excluded from Git)
├── main.py                # Main script for reading and saving data
├── requirements.txt       # Python dependencies
├── sensor_service.sh      # Optional script for managing service and venv
├── sensor.service         # (To be added) systemd unit file
└── README.md              # Project documentation
```

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Intellivisionn/ElectricNose-SensorReader.git
cd ElectricNose-SensorReader
```

### 2. Set Up Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the Reader (Manually)

```bash
python3 main.py
```

This will start reading from sensors and write output to:

```
/home/admin/ElectricNose-SensorReader/sensor_data.json
```

## ⚙️ Running as a Service

### Copy and Enable the systemd Service

```bash
sudo cp sensor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sensor.service
sudo systemctl start sensor.service
```

### Service Commands

```bash
sudo systemctl status sensor.service     # Check status
sudo systemctl restart sensor.service    # Restart the service
sudo systemctl stop sensor.service       # Stop the service
```

## 🧪 Logs & Output

- **Sensor Data:**  
  `/home/admin/ElectricNose-SensorReader/sensor_data.json`

- **Service Logs:**  
  `/home/admin/ElectricNose-SensorReader/sensor_service.log`

To monitor logs in real-time:

```bash
tail -f /home/admin/ElectricNose-SensorReader/sensor_service.log
```

## 🔁 Updating the Service

```bash
cd /home/admin/ElectricNose-SensorReader
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart sensor.service
```

## 🧠 Sensor Output Example

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

## 🛠️ Troubleshooting

- **Service not running?**  
  ```bash
  sudo systemctl status sensor.service
  ```

- **Dependency issues?**  
  Reinstall with:
  ```bash
  source venv/bin/activate
  pip install -r requirements.txt
  ```

- **Git pull fails?**  
  If offline, pull manually when back online and restart the service.

---

## 📜 License

This project is part of the Electric Nose system and is released under the MIT License.

---

**Developed for the Electric Nose project — Spring Semester 2025**
