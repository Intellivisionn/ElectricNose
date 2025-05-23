"""
This file is simply an example of how to connect everything together, when the predictor is ready @ Pauls and @ Martin
"""

import os
import sys
import asyncio
import random

from DataCollector.source.data_collector import SensorDataCollector
from OdourRecognizer.src.OdourRecognition import loadData
from OdourRecognizer.src.recognizers.RecognizerManager import RecognizerManager

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))

from DataCommunicator.source.WebSocketConnection import WebSocketConnection
from DataCommunicator.source.BaseDataClient   import BaseDataClient

SCENTS = ['lemon', 'coffee', 'vanilla', 'rose', 'smoke', 'earth']

class Predictor(BaseDataClient):
    def __init__(self, uri: str):
        # build the WS client but don’t connect yet
        super().__init__('predictor', WebSocketConnection(uri))
        self._state_q: asyncio.Queue[str] = asyncio.Queue()

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

            # PHASE 1: “unsure” for 5s
            t0 = loop.time()
            collector = SensorDataCollector()
            collector.start()
            while loop.time() - t0 < 180.0:
                await self.connection.send(
                    "topic:prediction",
                    {"scent": "loading", "confidence": "loading"}
                )
                await asyncio.sleep(0.5)

            # PHASE 2: random for 10s

            recognizer = RecognizerManager(models_folder_path="models")
            data = loadData("whasever")
            best_result = recognizer.recognize_best(data)
            await self.connection.send(
                "topic:prediction",
                {"scent": best_result['prediction'], "confidence": f"{best_result['confidence']:.2f}"}
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