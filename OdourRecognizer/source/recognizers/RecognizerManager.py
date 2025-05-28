import sys
from enum import Enum
import os
import numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))
from OdourRecognizer.source.recognizers.MLModel import MLModel

labels = {
    0: "Banana",
    1: "Blueberry",
    2: "Blood Orange",
    3: "Grape",
    4: "Lavender",
    5: "Pineapple"
}

class RecognizerManager:
    def __init__(self, models_folder_path):
        self.models = []
        for filename in os.listdir(models_folder_path):
            file_path = os.path.join(models_folder_path, filename)
            if os.path.isfile(file_path) and filename.endswith(".pkl"):
                self.models.append(MLModel(file_path))

    def recognize_all(self, data) -> list:
        probas = None
        for model in self.models:
            activeProbas = model.recognize(data)
            if probas is None:
                probas = activeProbas
            else:
                probas = np.add(probas, activeProbas)

        probas /= len(self.models)

        confidence = max(probas[0])
        
        prediction = labels[np.argmax(probas, axis=1)[0]]

        return prediction, confidence