import asyncio
import os
import time
from pathlib import Path

from IntegrationTests.mocks.BMEFake import BME680Sensor
from IntegrationTests.mocks.SGPFake import SGP30Sensor
from IntegrationTests.mocks.GroveFake import GroveGasSensor
from SensorReader.main import BaseSensorReader, SensorReaderClient
from IntegrationTests.mocks.FakeSensorDataLoader import FakeSensorDataLoader

class FakeElectronicNoseSensorReader(BaseSensorReader):
    def __init__(self, output_path, sleep_interval=2):
        loader = FakeSensorDataLoader(Path(__file__).parent / "data.json")
        sensors = [BME680Sensor(loader), SGP30Sensor(loader), GroveGasSensor(loader)]
        super().__init__(sensors, output_path, sleep_interval)

if __name__ == "__main__":
    project_dir = Path(__file__).resolve().parent
    output_path = project_dir / "sensor_data.json"
    reader = FakeElectronicNoseSensorReader(output_path, sleep_interval=1)

    uri = os.getenv('BROKER_URI', 'ws://localhost:8765')
    client = SensorReaderClient("sensor", uri, reader)

    # retry connect until broker is ready
    while True:
        try:
            asyncio.run(client.start())
            break
        except Exception as e:
            print(f"[SensorReaderFake] connect failed ({e}), retrying...")
            time.sleep(0.5)