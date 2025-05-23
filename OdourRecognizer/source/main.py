import json
import os
import sys
import asyncio
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))

from DataCollector.source.data_collector import SensorDataCollector
from OdourRecognizer.source.recognizers.RecognizerManager import RecognizerManager

from DataCommunicator.source.WebSocketConnection import WebSocketConnection
from DataCommunicator.source.BaseDataClient import BaseDataClient

class Predictor(BaseDataClient):
    def __init__(self, uri: str):
        # build the WS client but don’t connect yet
        super().__init__('predictor', WebSocketConnection(uri))
        self._state_q: asyncio.Queue[str] = asyncio.Queue()

    def prepareData(file_path) -> list[float]:
        with open(file_path, 'r') as data_file:
            data = json.load(data_file)

        timepoint_vectors = []

        for data_point in data[:90]:
            data_point_attr = []
            for sensor, readings in data_point.items():
                if sensor == "timestamp" or sensor == "SGP30Sensor":
                    continue
                elif sensor == "BME680Sensor":
                    for i, reading in enumerate(readings.values()):
                        if i in [0, 1, 2]:  # Skip temperature, pressure, humidity
                            continue
                        data_point_attr.append(reading)
                elif sensor == "GroveGasSensor":
                    for i, reading in enumerate(readings.values()):
                        if i in [4, 5]:  # Skip irrelevant channels
                            continue
                        data_point_attr.append(reading)
                else:
                    for reading in readings.values():
                        data_point_attr.append(reading)
            timepoint_vectors.append(data_point_attr)

        gradients = []
        for i in range(1, len(timepoint_vectors)):
            prev = np.array(timepoint_vectors[i - 1])
            curr = np.array(timepoint_vectors[i])
            gradient = (curr - prev).tolist()
            gradients.append(gradient)

        flattened_readings = [item for sublist in timepoint_vectors for item in sublist]
        flattened_gradients = [item for sublist in gradients for item in sublist]

        transformed_data = flattened_readings + flattened_gradients

        return transformed_data

    async def start(self):
        # explicitly open the WS connection
        await self.connection.connect()
        print("[predictor] connected")
        return await super().start()

    async def run(self):
        # subscribe to the state updates
        await self.connection.subscribe("state")
        print("[predictor] subscribed to state")

        # kick off our background loop
        asyncio.create_task(self._prediction_loop())

        # and stay alive
        while True:
            await asyncio.sleep(1)

    async def on_message(self, topic: str, payload: dict):
        # pick up your state broadcasts
        state = payload.get("state")
        if state:
            print(f"[predictor] got state → {state}")
            await self._state_q.put(state)

    async def _prediction_loop(self):
        loop = asyncio.get_event_loop()
        while True:
            # wait until IOHandler switches to PredictingState
            state = await self._state_q.get()
            if state != "PredictingState":
                continue

            print("[predictor] entering prediction phase")

            t0 = loop.time()
            collector = SensorDataCollector()
            collector.start()
            while loop.time() - t0 < 180.0:
                await self.connection.send(
                    "topic:prediction",
                    {"scent": "loading", "confidence": "loading"}
                )
                await asyncio.sleep(0.5)

            recognizer = RecognizerManager(models_folder_path="models")
            data = self.prepareData("test.json")
            result = recognizer.recognize(data)
            await self.connection.send(
                "topic:prediction",
                {"scent": result[0], "confidence": f"{result[1]:.2f}"}
            )
            await asyncio.sleep(0.5)

            print("[predictor] prediction phase complete — waiting for next PredictingState")

            # drain until IOHandler leaves PredictingState
            while True:
                new_state = await self._state_q.get()
                if new_state != "PredictingState":
                    break

if __name__ == "__main__":
    async def main():
        uri = "ws://localhost:8765"
        print(f"[predictor] starting → {uri}")
        p = Predictor(uri)
        await p.start()

    asyncio.run(main())