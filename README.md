# ElectricNose-DataReader

**DataReader** is a Python-based module designed for real-time sensor data collection and storage, built as part of the *Electric Nose* semester project. It continuously reads sensor data from a JSON file and saves it with timestamps for later processing and analysis.

## 📁 Features

- Reads live sensor data from a specified JSON file
- Appends timestamp to each reading
- Writes cumulative data to an output file
- Multi-threaded design with controlled read/write intervals
- Gracefully handles shutdown via `KeyboardInterrupt`
- Simple and portable — runs on any Python-enabled system (tested on Raspberry Pi 4)

## 🚀 Getting Started

### Prerequisites

- Python 3.6+
- A valid `sensor_data.json` file continuously updated by a sensor interface

### Installation

1. Clone this repository:

```bash
git clone https://github.com/yourusername/DataReader.git
cd DataReader
```

2. Run the script:

```bash
python3 main.py
```

You'll be prompted to enter a **scent name**, which will be used to name the output file (e.g., `mint_20250323_153012.json`).

## ⚙️ Configuration

By default, the script uses the following settings:

- Sensor JSON path: `/home/admin/ElectricNose-SensorReader/sensor_data.json`
- Output directory: `savedData`
- Read interval: 2 seconds
- Write interval: 5 seconds

These can be customized by modifying the `SensorDataCollector` initialization in `main.py`.

## 📂 Output

Collected data will be saved as a JSON array of timestamped entries:

```json
[
  {
    "sensor_value": 42,
    "timestamp": "2025-03-23T15:30:12.123456"
  }
]
```

## 🧠 Project Structure

```
DataReader/
├── main.py               # Entry point for starting the data collection
├── savedData/            # Automatically created; stores output files
└── README.md             # Project overview and usage guide
```

## 💡 Usage Tips

- Make sure the sensor data file is being updated continuously.
- Use `Ctrl+C` to stop the data collection gracefully.
- Ensure write permissions for the output directory.

## 📜 License

This project is part of an academic research project and is released under the MIT License.

---

**Developed for the Electric Nose project — Spring Semester 2025**
