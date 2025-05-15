# Example.py

import asyncio
import random

from WebSocketConnection import WebSocketConnection
from BaseDataClient import BaseDataClient

class SensorReaderClient(BaseDataClient):
    async def run(self):
        """Every second, send a fake sensor reading to 'collector'."""
        while True:
            reading = {'value': random.random()}
            print(f'[{self.name}] Sending: {reading}')
            await self.connection.send('collector', reading)
            await asyncio.sleep(1)

    async def on_message(self, frm, payload):
        print(f'[{self.name}] Received from {frm}: {payload}')

class DataCollectorClient(BaseDataClient):
    async def run(self):
        """Idle loop—we only react in on_message."""
        while True:
            await asyncio.sleep(1)

    async def on_message(self, frm, payload):
        if frm == 'sensor':
            # process incoming sensor data
            print(f'[{self.name}] Collected from {frm}: {payload}')
        print(f'[{self.name}] Collected {frm}: {payload}')

async def main():
    uri = 'ws://localhost:8765'

    # set up collector
    coll_conn = WebSocketConnection(uri)
    collector = DataCollectorClient('collector', coll_conn)

    # set up sensor
    sensor_conn = WebSocketConnection(uri)
    sensor = SensorReaderClient('sensors', sensor_conn)

    # run both clients concurrently
    await asyncio.gather(
        collector.start(),
        sensor.start(),
    )

if __name__ == '__main__':
    asyncio.run(main())