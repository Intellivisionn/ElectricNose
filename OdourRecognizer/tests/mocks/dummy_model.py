# generate_dummy_model.py
import joblib
from sklearn.ensemble import GradientBoostingClassifier
import numpy as np

X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
y = np.array([0, 1, 2, 1])

model = GradientBoostingClassifier()
model.fit(X, y)

joblib.dump(model, '../dummy_models/dummy_model.pkl')
