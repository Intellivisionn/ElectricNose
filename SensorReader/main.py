import sys, os
# insert project root (one level up from SensorReader/source) onto PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))

import time
import json
from pathlib import Path
from SensorReader.Sensors.SensorManager import SensorManager
from SensorReader.aspects.LoggingAspect import LoggingAspect
import board
from smbus2 import SMBus
from SensorReader.Sensors.BME680Sensor import BME680Sensor
from SensorReader.Sensors.SGP30Sensor import SGP30Sensor
from SensorReader.Sensors.GroveGasSensor import GroveGasSensor


class BaseSensorReader:
    def __init__(self, sensors, output_path, sleep_interval=2):
        self.sensors = sensors
        self.manager = SensorManager(self.sensors)
        self.output_path = output_path
        self.sleep_interval = sleep_interval

    @LoggingAspect.log_method
    def read_and_save(self):
        while True:
            self.read_and_save_once()
            time.sleep(self.sleep_interval)

    def read_and_save_once(self):
        data = self.manager.read_all()
        sensor_json = json.dumps(data, indent=4)
        with open(self.output_path, "w") as f:
            f.write(sensor_json)


class ElectricNoseSensorReader(BaseSensorReader):
    def __init__(self, output_path, sleep_interval=2):
        i2c = board.I2C()
        bus = SMBus(1)
        sensors = [
            BME680Sensor(i2c),
            SGP30Sensor(i2c),
            GroveGasSensor(bus)
        ]
        super().__init__(sensors, output_path, sleep_interval)

import asyncio
from DataCommunicator.source.WebSocketConnection import WebSocketConnection
from DataCommunicator.source.BaseDataClient import BaseDataClient

class SensorReaderClient(BaseDataClient):
    """
    Wraps the ElectricNoseSensorReader in a BaseDataClient to:
      1) write JSON to file (as before)
      2) send the same payload to 'collector' over WebSocket
    """
    def __init__(self, name: str, uri: str, reader: ElectricNoseSensorReader):
        conn = WebSocketConnection(uri)
        super().__init__(name, conn)
        self.reader = reader

    @LoggingAspect.log_method
    async def run(self):
        while True:
            # 1) read & save to JSON file
            self.reader.read_and_save_once()

            # 2) load the data back for sending
            with open(self.reader.output_path, "r") as f:
                data = json.load(f)

            # 3) send to the collector client
            await self.connection.send('collector', data)

            await asyncio.sleep(self.reader.sleep_interval)

    async def on_message(self, frm: str, payload: dict):
        # handle incoming messages if needed
        print(f'[{self.name}] Received control from {frm}: {payload}')


async def main():
    uri = 'ws://localhost:8765'
    project_dir = Path(__file__).resolve().parent
    output_path = project_dir / "sensor_data.json"

    # existing reader that writes to sensor_data.json
    reader = ElectricNoseSensorReader(output_path, sleep_interval=2)

    # new client that also forwards readings over WebSocket
    client = SensorReaderClient('sensor', uri, reader)

    await client.start()

if __name__ == "__main__":
    asyncio.run(main())