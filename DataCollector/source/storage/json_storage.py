import os, json
from DataCollector.source.storage.istorage import IStorage

class JSONStorage(IStorage):
    def __init__(self, output_file: str):
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        self.output_file = output_file

    def write(self, data: list) -> None:
        try:
            with open(self.output_file, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"[JSONStorage] Wrote {len(data)} records to {self.output_file}")
        except Exception as e:
            print(f"[JSONStorage] Write error: {e}")
