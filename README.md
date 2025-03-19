### Electric Nose Sensor Service - Documentation
**Project:** Electric Nose Sensor Reader  
**Location:** `/home/admin/ElectricNose-SensorReader/`  
**Service Name:** `sensor.service`  
**Primary Script:** `sensor.py`  

---

## 1. Service Overview
The **Electric Nose Sensor Service** is a systemd-managed process that:
1. **Automatically pulls updates** from GitHub (if online).
2. **Activates a Python virtual environment** for dependency management.
3. **Installs any missing dependencies**.
4. **Runs `sensor.py`**, which reads sensor data and logs it as JSON.

The sensor data is stored in `/home/admin/ElectricNose-SensorReader/sensor_data.json`, where external services can access it.

---

## 2. How to Use the Service
### Start the Service
```bash
sudo service sensor start
```

### Stop the Service
```bash
sudo service sensor stop
```

### Restart the Service
```bash
sudo service sensor restart
```

### Enable on Boot
```bash
sudo systemctl enable sensor.service
```

### Disable from Boot
```bash
sudo systemctl disable sensor.service
```

---

## 3. Log Management
The service logs its activity to:
- **Service Logs:** `/home/admin/ElectricNose-SensorReader/sensor_service.log`
- **Sensor Data JSON:** `/home/admin/ElectricNose-SensorReader/sensor_data.json`

### Viewing Logs
```bash
cat /home/admin/ElectricNose-SensorReader/sensor_service.log
```

Or, to follow the logs in real-time:
```bash
tail -f /home/admin/ElectricNose-SensorReader/sensor_service.log
```

View the latest 100 lines:
```bash
tail -n 100 /home/admin/ElectricNose-SensorReader/sensor_service.log
```

### Viewing System Logs
```bash
sudo journalctl -u sensor.service -n 50  # Last 50 logs
sudo journalctl -u sensor.service -f  # Follow logs in real-time
```

---

## 4. Sensor Data Storage
The script logs sensor readings in JSON format to:
```
/home/admin/ElectricNose-SensorReader/sensor_data.json
```
Example entry:
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
           ....
        }
    }
]
```

---

## 5. Updating the Service
To manually update:
```bash
cd /home/admin/ElectricNose-SensorReader
git pull
```

### Reinstall Dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Restart the Service
```bash
sudo service sensor restart
```

---

## 6. Troubleshooting
### Service Not Running?
Check if it’s active:
```bash
sudo systemctl status sensor.service
```

Start it if inactive:
```bash
sudo systemctl start sensor.service
```

### Logs Show "ModuleNotFoundError"?
Reinstall dependencies:
```bash
source /home/admin/ElectricNose-SensorReader/venv/bin/activate
pip install -r /home/admin/ElectricNose-SensorReader/requirements.txt
```
Then restart:
```bash
sudo systemctl restart sensor.service
```

### GitHub Pull Fails Due to No Network?
If offline, the service **skips `git pull`**. If you reconnect, restart the service:
```bash
sudo systemctl restart sensor.service
```

### Checking for Issues
1. View system logs:
   ```bash
   sudo journalctl -u sensor.service -n 50
   ```
2. View detailed service logs:
   ```bash
   cat /home/admin/ElectricNose-SensorReader/sensor_service.log
   ```

---

## 7. System Architecture
- **Sensor Service (`sensor.service`)**
  - Runs the script on boot.
  - Manages logging and updates.
  - Uses a virtual environment to isolate dependencies.

- **Sensor Script (`sensor.py`)**
  - Reads data from BME680, SGP30, and Grove sensors.
  - Formats the data as JSON.
  - Stores JSON data in `/home/admin/ElectricNose-SensorReader/sensor_data.json`.

- **Virtual Environment (`venv/`)**
  - Isolates Python dependencies.
  - Prevents conflicts with system-wide Python packages.

---
