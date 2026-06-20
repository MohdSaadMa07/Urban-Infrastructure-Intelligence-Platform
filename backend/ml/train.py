"""
Model training for UrbanIQ Phase 2.

Trains:
  - XGBClassifier -> risk classification (Low/Medium/High)
  - XGBRegressor  -> complaint count forecasting
  - DBSCAN        -> ward clustering for anomaly/pattern detection
"""

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier, XGBRegressor

from ml.utils import save_model, RISK_MODEL_PATH, FORECAST_MODEL_PATH, CLUSTER_MODEL_PATH, SCALER_PATH, FEATURES_PATH


def _label_encode(y_risk):
    mapping = {"Low": 0, "Medium": 1, "High": 2}
    return y_risk.map(mapping)


def train_risk_model(X, y_risk):
    """Train XGBClassifier for risk prediction. Returns (model, accuracy)."""
    y_enc = _label_encode(y_risk)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    save_model(scaler, SCALER_PATH)
    save_model(list(X.columns), FEATURES_PATH)

    model = XGBClassifier(
        n_estimators=150, max_depth=5, learning_rate=0.1,
        subsample=0.8, colsample_bytree=0.8,
        random_state=42, eval_metric="mlogloss",
    )
    model.fit(X_train_s, y_train)
    acc = model.score(X_test_s, y_test)
    print(f"  Risk model accuracy: {acc:.3f}")

    save_model(model, RISK_MODEL_PATH)
    print(f"  Saved: {RISK_MODEL_PATH.name}")
    return model, acc


def train_forecast_model(X, y_complaints):
    """Train XGBRegressor for complaint forecasting. Returns (model, R^2)."""
    y_risk_dummy = np.zeros(len(y_complaints))
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_complaints.values, test_size=0.2, random_state=42
    )

    from ml.utils import load_model
    scaler = load_model(SCALER_PATH)
    if scaler is None:
        raise RuntimeError("Train risk model first (scaler needed).")
    expected_cols = load_model(FEATURES_PATH)

    X_train_s = scaler.transform(X_train[expected_cols])
    X_test_s = scaler.transform(X_test[expected_cols])

    model = XGBRegressor(
        n_estimators=150, max_depth=5, learning_rate=0.1,
        subsample=0.8, colsample_bytree=0.8, random_state=42,
    )
    model.fit(X_train_s, y_train)
    r2 = model.score(X_test_s, y_test)
    print(f"  Forecast model R^2: {r2:.3f}")

    save_model(model, FORECAST_MODEL_PATH)
    print(f"  Saved: {FORECAST_MODEL_PATH.name}")
    return model, r2


def train_clustering(X):
    """Run DBSCAN clustering. Saves cluster metadata."""
    from ml.utils import load_model
    scaler = load_model(SCALER_PATH)
    expected_cols = load_model(FEATURES_PATH)
    X_s = scaler.transform(X[expected_cols])

    model = DBSCAN(eps=1.5, min_samples=3)
    labels = model.fit_predict(X_s)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)
    print(f"  DBSCAN: {n_clusters} clusters, {n_noise} noise points")

    save_model({
        "eps": 1.5, "min_samples": 3,
        "labels": labels.tolist(),
        "n_clusters": n_clusters, "n_noise": n_noise,
    }, CLUSTER_MODEL_PATH)
    print(f"  Saved: {CLUSTER_MODEL_PATH.name}")
    return model, labels
