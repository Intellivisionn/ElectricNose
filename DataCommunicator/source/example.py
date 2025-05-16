import asyncio
import random

from WebSocketConnection import WebSocketConnection
from BaseDataClient import BaseDataClient

class SensorReaderClient(BaseDataClient):
    async def run(self):
        """Every second, send a fake sensor reading to a topic and directly to a client."""
        await self.connection.subscribe('sensor_commands')  # listen to commands sent to this topic

        while True:
            reading = {'value': random.random()}
            print(f'[{self.name}] Sending: {reading}')

            # Send to specific client
            await self.connection.send('collector', reading)

            # Publish to a topic
            await self.connection.send('topic:sensor_readings', reading)

            # Broadcast to all clients
            await self.connection.broadcast({'from': self.name, 'value': reading['value']})

            await asyncio.sleep(1)

    async def on_message(self, frm, payload):
        print(f'[{self.name}] Received from {frm}: {payload}')
        # You could act on a control message like:
        if payload.get('cmd') == 'adjust':
            print(f'[{self.name}] Adjusting sensor config...')


class DataCollectorClient(BaseDataClient):
    async def run(self):
        """Subscribe to a topic and listen for sensor data."""
        await self.connection.subscribe('sensor_readings')
        while True:
            await asyncio.sleep(1)

    async def on_message(self, frm, payload):
        print(f'[{self.name}] Collected from {frm}: {payload}')
        # Optionally send control command back via topic
        if random.random() < 0.1:
            command = {'cmd': 'adjust'}
            print(f'[{self.name}] Sending control: {command}')
            await self.connection.send('topic:sensor_commands', command)


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