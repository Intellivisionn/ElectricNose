import joblib
import os

class MLModel:
    def __init__(self, model_path="models/model.pkl"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at: {model_path}")
        self.model = joblib.load(model_path)