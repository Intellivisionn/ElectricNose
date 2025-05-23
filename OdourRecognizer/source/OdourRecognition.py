import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))

from OdourRecognizer.src.recognizers.RecognizerManager import RecognizerManager

recognizer = RecognizerManager(models_folder_path="models")

data = loadData("test.json")

best_result = recognizer.recognize(data)

print(f"Prediction: {best_result[0]}")
print(f"Confidence: {best_result[1]:.2f}")
