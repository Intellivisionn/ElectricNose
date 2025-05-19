import sys
import os
import json
import time
import threading
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from DataCollector.source.data_collector import SensorDataCollector
from DataCollector.source.storage.json_storage import JSONStorage
from DataCollector.source.storage_manager import StorageManager


@pytest.fixture
def temp_output_dir(tmp_path):
    return tmp_path


def test_collector_initialization_creates_file_path(temp_output_dir):
    collector = SensorDataCollector(scent_name="peach", output_dir=str(temp_output_dir))
    assert collector.scent_name == "peach"
    assert os.path.basename(collector.json_file).startswith("peach_")
    assert os.path.dirname(collector.json_file) == str(temp_output_dir)


def test_constructor_prompts_when_no_scent(monkeypatch, tmp_path):
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _: "mango")

    collector = SensorDataCollector(scent_name=None, output_dir=str(tmp_path))
    assert collector.scent_name == "mango"
    assert "mango" in collector.json_file


def test_json_storage_writes_correctly(temp_output_dir):
    file_path = temp_output_dir / "output.json"
    storage = JSONStorage(str(file_path))

    data = [{"sensor": "mock", "value": 42}]
    storage.write(data)

    with open(file_path) as f:
        content = json.load(f)

    assert isinstance(content, list)
    assert content[0]["sensor"] == "mock"
    assert content[0]["value"] == 42


def test_storage_manager_writes_from_datasource(temp_output_dir):
    class DummyCollector:
        def __init__(self):
            self.stop_event = threading.Event()
            self.data_lock = threading.Lock()
            self.sensor_data_list = [{"sensor": "temp", "value": 10}]

    class DummyStorage:
        def __init__(self):
            self.written = []

        def write(self, data):
            self.written.append(data)

    collector = DummyCollector()
    storage = DummyStorage()

    manager = StorageManager([storage], data_source=collector, interval=0.1)

    def stop_soon():
        time.sleep(0.2)
        collector.stop_event.set()

    threading.Thread(target=stop_soon).start()
    manager.start()
    manager.join()

    assert len(storage.written) >= 1
    assert {"sensor": "temp", "value": 10} in storage.written[0]


def test_receiver_client_appends_data():
    collector = SensorDataCollector(scent_name="test", output_dir=".")
    receiver = collector._ReceiverClient(collector)

    payload = {"sensor": "humidity", "value": 55}
    asyncio_run(receiver.on_message("mock", payload))

    with collector.data_lock:
        assert len(collector.sensor_data_list) == 1
        assert collector.sensor_data_list[0]["sensor"] == "humidity"
        assert "timestamp" in collector.sensor_data_list[0]


def test_start_handles_keyboard_interrupt(monkeypatch, tmp_path, capfd):
    # Use a dummy receiver with no-op start()
    class DummyReceiver:
        async def start(self): pass

    # Patch receiver with dummy
    collector = SensorDataCollector(scent_name="banana", output_dir=str(tmp_path))
    collector.receiver = DummyReceiver()

    # Patch StorageManager to track calls
    class DummyStorage:
        def __init__(self): self.written = []

        def write(self, data): self.written.append(data)

    class DummyStorageManager(threading.Thread):
        def __init__(self, *args, **kwargs):
            super().__init__(daemon=True)
            self.calls = []
            self.collector = kwargs["data_source"]
            self.interval = kwargs["interval"]

        def run(self):
            self.calls.append("run")
            time.sleep(0.1)
            self.collector.stop_event.set()

    monkeypatch.setattr("DataCollector.source.data_collector.StorageManager", DummyStorageManager)

    # Simulate immediate KeyboardInterrupt by patching sleep
    monkeypatch.setattr(time, "sleep", lambda x: (_ for _ in ()).throw(KeyboardInterrupt))

    collector.start(write_interval=0.1)

    out = capfd.readouterr().out
    assert "Stopping data collection" in out


# Helper to run async code safely
def asyncio_run(coro):
    import asyncio
    try:
        return asyncio.run(coro)
    except RuntimeError:  # fallback for IDEs with active loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
