import json
import os
import sys
import asyncio
import numpy as np
from datetime import datetime

import concurrent.futures
from functools import partial   

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))

from DataCollector.source.data_collector import SensorDataCollector
from OdourRecognizer.source.recognizers.RecognizerManager import RecognizerManager

from DataCommunicator.source.WebSocketConnection import WebSocketConnection
from DataCommunicator.source.BaseDataClient import BaseDataClient

class Predictor(BaseDataClient):
    def __init__(self, uri: str):
        super().__init__('predictor', WebSocketConnection(uri))
        self._state_q: asyncio.Queue[str] = asyncio.Queue()
        self._data_q: asyncio.Queue[dict] = asyncio.Queue() 
        self.prediction_active = False
        self.data = []
        self.current_state = None  # Add current state tracking

    def prepareData(self, data: list) -> list[float]:
        # Modified to accept dict instead of file path
        timepoint_vectors = []
        REQUIRED_SAMPLES = 90  # Define constant for required samples

        # Check if we have enough data
        if len(data) < REQUIRED_SAMPLES:
            raise ValueError(f"Not enough data points. Have {len(data)}, need {REQUIRED_SAMPLES}")

        # Pad data if necessary
        if len(data) < REQUIRED_SAMPLES:
            # Duplicate the last entry to pad
            last_entry = data[-1]
            while len(data) < REQUIRED_SAMPLES:
                data.append(last_entry.copy())

        # Take exactly REQUIRED_SAMPLES samples
        data = data[-REQUIRED_SAMPLES:]  # Take the most recent samples

        for data_point in data:
            data_point_attr = []
            for sensor, readings in data_point.items():
                if sensor == "timestamp" or sensor == "SGP30Sensor":
                    continue
                elif sensor == "BME680Sensor":
                    for i, reading in enumerate(readings.values()):
                        if i in [0, 1, 2]:
                            continue
                        data_point_attr.append(float(reading))
                elif sensor == "GroveGasSensor":
                    for i, reading in enumerate(readings.values()):
                        if i in [4, 5]:
                            continue
                        data_point_attr.append(float(reading))
                else:
                    for reading in readings.values():
                        data_point_attr.append(float(reading))
            timepoint_vectors.append(data_point_attr)

        gradients = []
        for i in range(1, len(timepoint_vectors)):
            prev = np.array(timepoint_vectors[i - 1])
            curr = np.array(timepoint_vectors[i])
            gradient = (curr - prev).tolist()
            gradients.append(gradient)

        flattened_readings = [item for sublist in timepoint_vectors for item in sublist]
        flattened_gradients = [item for sublist in gradients for item in sublist]

        final_vector = flattened_readings + flattened_gradients
        
        # Verify the feature count
        EXPECTED_FEATURES = 895  # The number of features the model expects
        if len(final_vector) != EXPECTED_FEATURES:
            raise ValueError(f"Feature mismatch. Generated {len(final_vector)} features, model expects {EXPECTED_FEATURES}")

        return final_vector

    async def start(self):
        # explicitly open the WS connection
        await self.connection.connect()
        print("[predictor] connected")
        return await super().start()

    async def run(self):
        await self.connection.subscribe("state")
        await self.connection.subscribe("sensor_readings")
        print("[predictor] subscribed to state and sensor_readings")

        # Only create prediction loop task
        asyncio.create_task(self._prediction_loop())

        # and stay alive
        while True:
            await asyncio.sleep(1)

    async def on_message(self, frm: str, payload: dict):
        if frm == 'io':  # State messages from io
            state = payload.get("state")
            if state:
                print(f"[predictor] got state → {state}")
                self.current_state = state  # Update current state
                await self._state_q.put(state)
                
                # Clear data when entering LoadingState
                if state == "LoadingState":
                    print("[predictor] clearing data for LoadingState")
                    self.data = []
                    self.prediction_active = False
                    
        elif frm == 'sensor':
            payload['timestamp'] = datetime.now().isoformat()
            # Only collect data during LoadingState
            if self.current_state == "LoadingState":
                self.data.append(payload)
                print(f"[Collector] Received from {frm}: {payload}")
                print(f"[Collector] Data length: {len(self.data)}")

    async def _prediction_loop(self):
        while True:
            try:
                # Wait for state change
                state = await self._state_q.get()
                
                if state == "LoadingState":
                    print("[predictor] in loading state, clearing data")
                    self.data = []
                    self.prediction_active = False
                    continue
                    
                if state != "PredictingState":
                    continue

                print("[predictor] entering prediction phase")
                self.prediction_active = True

                try:
                    data = self.data
                    
                    print(f"[predictor] processing data (collected {len(data)} samples)")
                    models_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
                    
                    if not os.path.exists(models_path):
                        raise FileNotFoundError(f"Models directory not found at: {models_path}")

                    if len(data) < 90:
                        print(f"[predictor] WARNING: Not enough data points ({len(data)}), waiting for more data")
                        await self.connection.send(
                            "topic:prediction",
                            {"scent": "waiting", "confidence": "insufficient data"}
                        )
                        continue

                    # Create thread pool
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        # Start sending "processing" messages
                        while self.current_state == "PredictingState":
                            await self.connection.send(
                                "topic:prediction",
                                {"scent": "processing", "confidence": "calculating"}
                            )
                            
                            # Run the heavy processing in a separate thread
                            future = pool.submit(self._process_prediction, data, models_path)
                            
                            try:
                                # Wait for the result with a timeout
                                result = await asyncio.get_event_loop().run_in_executor(
                                    None, 
                                    future.result,
                                    1  # 1 second timeout
                                )
                                
                                if result:
                                    # Send prediction for 10 seconds
                                    t_end = asyncio.get_event_loop().time() + 10.0
                                    while asyncio.get_event_loop().time() < t_end:
                                        if self.current_state != "PredictingState":
                                            break
                                        await self.connection.send(
                                            "topic:prediction",
                                            {"scent": result[0], "confidence": f"{result[1]:.2f}"}
                                        )
                                        await asyncio.sleep(0.5)
                                    print(f"[predictor] prediction complete: {result}")
                                    break
                                
                            except concurrent.futures.TimeoutError:
                                await asyncio.sleep(0.5)  # Wait before sending next processing message
                                continue

                except ValueError as e:
                    print(f"[predictor] Data processing error: {str(e)}")
                    await self.connection.send(
                        "topic:prediction",
                        {"scent": "error", "confidence": "data processing error"}
                    )
                except Exception as e:
                    print(f"[predictor] Unexpected error: {str(e)}")
                    await self.connection.send(
                        "topic:prediction",
                        {"scent": "error", "confidence": "processing error"}
                    )

            except Exception as e:
                print(f"[predictor] Critical error in prediction loop: {str(e)}")
                await asyncio.sleep(1)
            finally:
                self.prediction_active = False
                print("[predictor] prediction phase complete — waiting for next PredictingState")

    def _process_prediction(self, data, models_path):
        """Run the prediction processing in a separate thread"""
        try:
            recognizer = RecognizerManager(models_folder_path=models_path)
            processed_data = self.prepareData(data)
            return recognizer.recognize(processed_data)
        except Exception as e:
            print(f"[predictor] Error in prediction thread: {str(e)}")
            return None

    async def _send_processing_status(self):
        """Send processing status messages while prediction is being calculated"""
        try:
            while True:
                await self.connection.send(
                    "topic:prediction",
                    {"scent": "processing", "confidence": "calculating"}
                )
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            # Task was cancelled, which is expected
            pass

if __name__ == "__main__":
    async def main():
        uri = "ws://localhost:8765"
        print(f"[predictor] starting → {uri}")
        p = Predictor(uri)
        await p.start()

    asyncio.run(main())