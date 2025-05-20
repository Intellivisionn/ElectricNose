import joblib
import os

class MLModel:
    def __init__(self, model_path="models/model.pkl"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at: {model_path}")
        self.model = joblib.load(model_path)
        self.model_name = type(self.model).__name__

    def predict(self, features):
        prediction = self.model.predict([features])[0]

        # If the model supports predict_proba, get confidence
        if hasattr(self.model, "predict_proba"):
            probabilities = self.model.predict_proba([features])[0]
            confidence = max(probabilities)
        else:
            confidence = None  # fallback if model doesn't support it

        return {
            "model_name": self.model_name,
            "prediction": prediction,
            "confidence": confidence
        }