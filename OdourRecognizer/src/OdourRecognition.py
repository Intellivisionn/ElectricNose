import json
import os

import numpy as np

from OdourRecognizer.src.recognizers.RecognizerManager import RecognizerManager



# load
def transform(file_path) -> list[float]:
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


def loadData(path) -> list[list]:
    full_data = []

    for f in os.listdir(path):
        if f.endswith('.json'):
            file_path = os.path.join(path, f)
            transformed_data = transform(file_path)
            full_data.append(transformed_data)

    return full_data


recognizer = RecognizerManager(models_folder_path="models")

data = loadData("whasever")

best_result = recognizer.recognize_best(data)

print(f"Best Model: {best_result['model_name']}")
print(f"Prediction: {best_result['prediction']}")
print(f"Confidence: {best_result['confidence']:.2f}")
