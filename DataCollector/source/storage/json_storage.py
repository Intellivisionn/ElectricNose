import os, json
from datetime import datetime

from DataCollector.source.storage.istorage import IStorage

class JSONStorage(IStorage):
    def __init__(self, output_dir: str = "savedData"):
        self.output_file = None
        self.output_dir = output_dir

    def write(self, data: list) -> None:
        try:
            with open(self.output_file, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"[JSONStorage] Wrote {len(data)} records to {self.output_file}")
        except Exception as e:
            print(f"[JSONStorage] Write error: {e}")

    def set_filename(self, scent_name) -> None:
        # prepare JSON output path
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_file = os.path.join(self.output_dir, f"{scent_name}_{ts}.json")
