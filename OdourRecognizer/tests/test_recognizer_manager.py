import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from OdourRecognizer.source.recognizers.RecognizerManager import RecognizerManager

class FakeModel:
    def __init__(self, return_value):
        self.return_value = return_value

    def recognize(self, data):
        return np.array([self.return_value])

class TestRecognizerManager:
    @patch("OdourRecognizer.source.recognizers.RecognizerManager.os.listdir")
    @patch("OdourRecognizer.source.recognizers.RecognizerManager.os.path.isfile")
    @patch("OdourRecognizer.source.recognizers.RecognizerManager.MLModel")
    def test_init_loads_models(self, mock_mlmodel, mock_isfile, mock_listdir):
        mock_listdir.return_value = ["model1.pkl", "model2.pkl", "not_model.txt"]
        mock_isfile.side_effect = lambda path: path.endswith(".pkl")

        fake_model_instance = MagicMock()
        mock_mlmodel.return_value = fake_model_instance

        manager = RecognizerManager("models/")
        assert len(manager.models) == 2
        assert all(m == fake_model_instance for m in manager.models)

    def test_recognize_all_correct_label_selection(self, monkeypatch):
        # Bypass init
        manager = RecognizerManager.__new__(RecognizerManager)

        # Fake models return different probabilities
        manager.models = [
            FakeModel([0.1, 0.7, 0.1, 0.05, 0.03, 0.02]),  # Blueberry strongest
            FakeModel([0.2, 0.6, 0.1, 0.05, 0.03, 0.02]),  # Blueberry still strongest
            FakeModel([0.3, 0.5, 0.1, 0.05, 0.03, 0.02]),  # Closer, but Blueberry wins
        ]

        # Patch labels
        monkeypatch.setattr("OdourRecognizer.source.recognizers.RecognizerManager.labels", {
            0: "Banana",
            1: "Blueberry",
            2: "Blood Orange",
            3: "Grape",
            4: "Lavender",
            5: "Pineapple"
        })

        prediction, confidence = manager.recognize_all([1, 2, 3])

        # Blueberry has the highest average confidence
        assert prediction == "Blueberry"
        expected_avg = (0.7 + 0.6 + 0.5) / 3
        assert abs(confidence - expected_avg) < 0.0001
