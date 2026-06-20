"""
Preprocessing utilities for inference.

For training, scaling is handled inside ml/train.py directly.
This module is used by ml/predict.py during prediction generation.
"""

from ml.utils import load_model, SCALER_PATH, FEATURES_PATH


def scale_features(X):
    """
    Scale features using the saved StandardScaler.
    Used during prediction (inference).
    """
    scaler = load_model(SCALER_PATH)
    expected_cols = load_model(FEATURES_PATH)
    if scaler is None or expected_cols is None:
        raise RuntimeError("No trained scaler found. Run `python manage.py train_models` first.")
    X = X.reindex(columns=expected_cols, fill_value=0)
    return scaler.transform(X)
