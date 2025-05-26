import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(__file__, '..', '..', '..')))

from OdourRecognizer.source.recognizers.MLModel import MLModel

class TestMLModel:
    @patch("OdourRecognizer.source.recognizers.MLModel.joblib.load")
    def test_mlmodel_init_loads_model(self, mock_load):
        mock_model = MagicMock()
        mock_load.return_value = mock_model

        model = MLModel("OdourRecognizer/tests/dummy_models/dummy_model.pkl")
        assert model.model == mock_model

    def test_mlmodel_init_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            MLModel("models/does_not_exist.pkl")

    @patch("OdourRecognizer.source.recognizers.MLModel.joblib.load")
    def test_mlmodel_recognize(self, mock_load):
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = [[0.1, 0.9]]
        mock_load.return_value = mock_model

        model = MLModel("OdourRecognizer/tests/dummy_models/dummy_model.pkl")
        result = model.recognize([1, 2, 3])

        assert result == [[0.1, 0.9]]
        mock_model.predict_proba.assert_called_once_with([[1, 2, 3]])

