import os

from OdourRecognizer.src.recognizers.MLModel import MLModel


class RecognizerManager:
    def __init__(self, models_folder_path):
        self.models = []
        for filename in os.listdir(models_folder_path):
            file_path = os.path.join(models_folder_path, filename)
            if os.path.isfile(file_path) and filename.endswith(".pkl"):
                self.models.append(MLModel(file_path))

    def recognize_all(self, data) -> list:
        all_predictions = []
        for model in self.models:
            prediction = model.recognize(data)
            all_predictions.append(prediction)
        return all_predictions

    def recognize_best(self, data) -> dict:
        """Return the prediction with the highest confidence."""
        predictions = self.recognize_all(data)
        if not predictions:
            return {"model_name": None, "prediction": None, "confidence": 0.0}
        best = max(predictions, key=lambda x: x["confidence"])
        return best