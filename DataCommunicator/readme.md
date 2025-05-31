#  Example

This is an example demonstrating how to use a WebSocket-based message broker system in a fake, simulating sensor data transmission and collection.

## Overview

The code below defines two clients:

- **SensorReaderClient**: 
  - Simulates a sensor that generates random readings.
  - Sends data to a topic and directly to another client.
  - Responds to control commands.

- **DataCollectorClient**:
  - Listens to a topic and collects data from sensors.
  - Occasionally sends control commands back.

Both clients use:
- `WebSocketConnection` — a WebSocket-based connection to the broker.
- `BaseDataClient` — a base class that manages the client lifecycle and handles incoming messages.

## Full Example Code

```python
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
        if random.random() < 0.1:
            command = {'cmd': 'adjust'}
            print(f'[{self.name}] Sending control: {command}')
            await self.connection.send('topic:sensor_commands', command)

async def main():
    uri = 'ws://localhost:8765'

    coll_conn = WebSocketConnection(uri)
    collector = DataCollectorClient('collector', coll_conn)

    sensor_conn = WebSocketConnection(uri)
    sensor = SensorReaderClient('sensors', sensor_conn)

    await asyncio.gather(
        collector.start(),
        sensor.start(),
    )

if __name__ == '__main__':
    asyncio.run(main())
```