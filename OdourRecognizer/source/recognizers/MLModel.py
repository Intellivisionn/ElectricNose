import joblib
import os
from OdourRecognizer.source.recognizers.RecognizeInterface import RecognizeInterface

class MLModel(RecognizeInterface):
    def __init__(self, model_path="models/model.pkl"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at: {model_path}")
        self.model = joblib.load(model_path)

    def recognize(self, data):
        return self.model.predict_proba([data])