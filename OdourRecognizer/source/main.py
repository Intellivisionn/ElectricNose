import json
import os
import sys
import asyncio
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))

from DataCollector.source.data_collector import SensorDataCollector
from OdourRecognizer.source.recognizers.RecognizerManager import RecognizerManager

from DataCommunicator.source.WebSocketConnection import WebSocketConnection
from DataCommunicator.source.BaseDataClient import BaseDataClient

class Predictor(BaseDataClient):
    def __init__(self, uri: str):
        # build the WS client but don't connect yet
        super().__init__('predictor', WebSocketConnection(uri))
        self._state_q: asyncio.Queue[str] = asyncio.Queue()
        self._data_q: asyncio.Queue[dict] = asyncio.Queue() 
        self.prediction_active = False
        self.data = []

    def prepareData(self, data: list) -> list[float]:
        # Modified to accept dict instead of file path
        timepoint_vectors = []

        for data_point in data[:90]:
            data_point_attr = []
            for sensor, readings in data_point.items():
                if sensor == "timestamp" or sensor == "SGP30Sensor":
                    continue
                elif sensor == "BME680Sensor":
                    for i, reading in enumerate(readings.values()):
                        if i in [0, 1, 2]:
                            continue
                        data_point_attr.append(reading)
                elif sensor == "GroveGasSensor":
                    for i, reading in enumerate(readings.values()):
                        if i in [4, 5]:
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

        return flattened_readings + flattened_gradients

    async def start(self):
        # explicitly open the WS connection
        await self.connection.connect()
        print("[predictor] connected")
        return await super().start()

    async def run(self):
        # subscribe to the state updates
        await self.connection.subscribe("state")
        await self.connection.subscribe("sensor_readings")
        print("[predictor] subscribed to state and completedata")

        # kick off our background loop
        asyncio.create_task(self._prediction_loop())

        # and stay alive
        while True:
            await asyncio.sleep(1)

    async def on_message(self, frm: str, payload: dict):
        if frm == 'io':  # State messages from io
            state = payload.get("state")
            if state:
                print(f"[predictor] got state → {state}")
                await self._state_q.put(state)
        elif frm == 'sensor':
            payload['timestamp'] = datetime.now().isoformat()
            self.data.append(payload)
            print(f"[Collector] Received from {frm}: {payload}")
            print(f"[Collector] Data length: {len(self.data)}")


    async def _prediction_loop(self):
        while True:
            # Wait for PredictingState
            state = await self._state_q.get()
            if state != "PredictingState":
                continue

            print("[predictor] entering prediction phase")
            self.prediction_active = True

            try:
                data = self.data
                
                # Process the data
                print("[predictor] processing data")
                models_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
                recognizer = RecognizerManager(models_folder_path=models_path)
                processed_data = self.prepareData(data)
                result = recognizer.recognize(processed_data)

                # Send prediction for 10 seconds
                t_end = asyncio.get_event_loop().time() + 10.0
                while asyncio.get_event_loop().time() < t_end:
                    await self.connection.send(
                        "topic:prediction",
                        {"scent": result[0], "confidence": f"{result[1]:.2f}"}
                    )
                    await asyncio.sleep(0.5)
                print(f"[predictor] prediction phase complete {result}")

            except asyncio.TimeoutError:
                print("[predictor] timeout waiting for complete data")
                await self.connection.send(
                    "topic:prediction",
                    {"scent": "error", "confidence": "timeout"}
                )

            finally:
                self.prediction_active = False
                print("[predictor] prediction phase complete — waiting for next PredictingState")

            # Clear state queue until we leave PredictingState
            while True:
                new_state = await self._state_q.get()
                if new_state != "PredictingState":
                    break

    async def _loading_loop(self):
        while True:
            # Wait for LoadingState
            state = await self._state_q.get()
            if state != "LoadingState":
                continue

            self.data = []
            self.prediction_active = False

            print("[predictor] entering loading phase")
            

if __name__ == "__main__":
    async def main():
        uri = "ws://localhost:8765"
        print(f"[predictor] starting → {uri}")
        p = Predictor(uri)
        await p.start()

    asyncio.run(main())