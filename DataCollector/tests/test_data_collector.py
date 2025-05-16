import sys
import types
import threading
import time
import json
import os
import pytest
from datetime import datetime

# ─── Stub DataCommunicator so imports in data_collector.py succeed ───
DataCommunicator = types.ModuleType('DataCommunicator')
DataCommunicator.source = types.ModuleType('DataCommunicator.source')

# Stub WebSocketConnection
ws_mod = types.ModuleType('DataCommunicator.source.WebSocketConnection')
class StubWebSocketConnection:
    def __init__(self, uri): pass
    def set_client(self, client): pass
    async def connect(self): pass
ws_mod.WebSocketConnection = StubWebSocketConnection

# Stub BaseDataClient
bdc_mod = types.ModuleType('DataCommunicator.source.BaseDataClient')
class StubBaseDataClient:
    def __init__(self, name, conn): pass
    async def start(self): pass
bdc_mod.BaseDataClient = StubBaseDataClient

sys.modules['DataCommunicator'] = DataCommunicator
sys.modules['DataCommunicator.source'] = DataCommunicator.source
sys.modules['DataCommunicator.source.WebSocketConnection'] = ws_mod
sys.modules['DataCommunicator.source.BaseDataClient']    = bdc_mod

# ─── Now import the class under test ───
from source.data_collector import SensorDataCollector

class TestSensorDataCollector:

    def test_constructor_uses_input_when_no_scent(self, tmp_path, monkeypatch):
        # Simulate interactive terminal
        monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
        # Patch input() to return a custom scent name
        monkeypatch.setattr('builtins.input', lambda prompt: 'my_scent')
        outdir = str(tmp_path / "outdir")
        collector = SensorDataCollector(
            scent_name=None,
            output_dir=outdir,
            write_interval=3
        )
        assert collector.scent_name == 'my_scent'
        base = os.path.basename(collector.output_file)
        assert base.startswith('my_scent_')
        assert os.path.dirname(collector.output_file) == outdir

    def test_write_sensor_data_error_path(self, tmp_path, capfd, monkeypatch):
        # Write to a path that can't be opened => triggers exception branch
        collector = SensorDataCollector(
            scent_name="s",
            output_dir=str(tmp_path),
            write_interval=1
        )
        # Prime data list so write_sensor_data tries to open
        collector.sensor_data_list = [{'x': 1}]
        # Patch open() to raise
        monkeypatch.setattr('builtins.open', lambda *args, **kw: (_ for _ in ()).throw(IOError("disk full")))
        collector.write_sensor_data("irrelevant.json")
        out = capfd.readouterr().out
        assert "Error writing to JSON file: disk full" in out

    def test_start_handles_keyboard_interrupt(self, tmp_path, monkeypatch, capfd):
        # Make sure threads are stubbed
        collector = SensorDataCollector(
            scent_name="s",
            output_dir=str(tmp_path),
            write_interval=1
        )
        calls = []

        # Stub receiver.start so it records its call, then returns
        async def fake_receiver_start():
            calls.append('recv_start')
        monkeypatch.setattr(collector.receiver, 'start', fake_receiver_start)

        # Stub the writer thread class so we can track init/start/join
        class DummyWriter:
            def __init__(self, col, out, interval):
                calls.append(('writer_init', out, interval))
            def start(self):
                calls.append('writer_started')
            def join(self):
                calls.append('writer_joined')
        monkeypatch.setattr(collector, 'SensorWriterThread', DummyWriter)

        # Make the very first sleep in start() raise KeyboardInterrupt
        def sleep_side(sec):
            raise KeyboardInterrupt
        monkeypatch.setattr(time, 'sleep', sleep_side)

        # Run start(); it should catch KeyboardInterrupt and do cleanup
        collector.start()

        out = capfd.readouterr().out
        assert "Stopping data collection..." in out

        # Validate the sequence of calls
        assert 'recv_start' in calls
        assert ('writer_init', collector.output_file, collector.write_interval) in calls
        assert 'writer_started' in calls
        assert 'writer_joined' in calls

    def test_sensor_writer_thread_happy_path(self, tmp_path):
        # Exactly your existing writer-thread test
        collector = SensorDataCollector(
            scent_name="s",
            output_dir=str(tmp_path),
            write_interval=0.05
        )
        collector.sensor_data_list = [
            {"x": 42, "timestamp": datetime.now().isoformat()}
        ]
        # Stop after ~0.1s
        def stopper():
            time.sleep(0.1)
            collector.stop_event.set()
        threading.Thread(target=stopper).start()

        writer = collector.SensorWriterThread(
            collector,
            collector.output_file,
            write_interval=0.05
        )
        writer.start()
        writer.join()

        with open(collector.output_file) as f:
            data = json.load(f)
        assert isinstance(data, list) and len(data) >= 1

    def test_receiver_on_message_appends_payload(self):
        # Directly exercise the on_message path
        collector = SensorDataCollector(
            scent_name="s",
            output_dir=".",
            write_interval=1
        )
        payload = {"foo": 123}
        # Simulate incoming WebSocket message
        import asyncio
        asyncio.run(collector.receiver.on_message("sensor", payload))

        assert collector.sensor_data_list[-1]["foo"] == 123
        assert "timestamp" in collector.sensor_data_list[-1]