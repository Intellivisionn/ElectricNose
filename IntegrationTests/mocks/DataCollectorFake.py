import os
import sys
from pathlib import Path
from DataCollector.source.data_collector import SensorDataCollector

if __name__ == "__main__":
    scent_arg = sys.argv[1] if len(sys.argv) >= 2 else None
    write_interval = int(os.getenv("WRITE_INTERVAL", "1"))
    output_dir = Path(__file__).resolve().parent / "savedData"

    collector = SensorDataCollector(
        scent_name=scent_arg,
        output_dir=output_dir,
        write_interval=write_interval
    )
    collector.start()