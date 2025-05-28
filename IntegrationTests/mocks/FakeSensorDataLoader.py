import json
from pathlib import Path

class FakeSensorDataLoader:
    def __init__(self, path: Path):
        with open(path, 'r') as f:
            self._data = json.load(f)
        self._index = 0

    def next(self):
        if not self._data:
            raise ValueError("No fake sensor data loaded.")

        record = self._data[self._index]
        self._index = (self._index + 1) % len(self._data)  # cycle
        return record