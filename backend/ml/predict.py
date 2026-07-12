"""
Prediction generation for all wards.

Loads trained models and generates:
  - Risk classification
  - Complaint forecast (with prediction intervals)
  - DBSCAN cluster assignment
  - Health score
  - Recommendation
  - Per-ward top contributing features

Supports two forecast horizons via separate models:
  - horizon=1: forecasts 1 year ahead (N+1 models)
  - horizon=2: forecasts 2 years ahead (N+2 models)
"""

import numpy as np
import pandas as pd

from ml.features import build_feature_matrix
from ml.preprocess import scale_features
from ml.recommendations import generate_recommendation
from ml.utils import (
    load_model,
    RISK_MODEL_PATH,
    FORECAST_MODEL_PATH,
    FORECAST_LOWER_PATH,
    FORECAST_UPPER_PATH,
    FORECAST_N2_MODEL_PATH,
    FORECAST_N2_LOWER_PATH,
    FORECAST_N2_UPPER_PATH,
    SCALER_PATH,
    FEATURES_PATH,
)


def _top_features(feature_values, feature_names, n=3):
    """
    Compute per-ward top contributing features.
    Uses absolute feature value * global feature importance as heuristic.
    """
    risk_model = load_model(RISK_MODEL_PATH)
    if risk_model is None or not hasattr(risk_model, 'feature_importances_'):
        return None
    if isinstance(feature_values, pd.DataFrame):
        values = feature_values.iloc[0].values
    elif isinstance(feature_values, pd.Series):
        values = feature_values.values
    else:
        values = np.asarray(feature_values).ravel()
    importance = risk_model.feature_importances_
    weighted = np.abs(values) * importance
    top_idx = np.argsort(weighted)[::-1][:n]
    return [
        {"feature": feature_names[i], "weight": round(float(weighted[i]), 1)}
        for i in top_idx
        if weighted[i] > 0
    ]


def generate_predictions(target_year=None, horizon=1):
    """
    Generate predictions for all wards for a target year.

    Args:
        target_year: year to predict for (default: latest CivicMetrics year + horizon)
        horizon: 1 for one-year-ahead, 2 for two-years-ahead

    Returns:
        list of prediction dicts, target_year
    """
    if target_year is None:
        from api.models import CivicMetrics
        latest = CivicMetrics.objects.order_by("-year").values_list("year", flat=True).first()
        target_year = (latest or 2026) + horizon

    # Load risk model (shared across horizons)
    risk_model = load_model(RISK_MODEL_PATH)

    # Load horizon-specific forecast models
    if horizon == 2:
        forecast_model = load_model(FORECAST_N2_MODEL_PATH)
        forecast_lower = load_model(FORECAST_N2_LOWER_PATH)
        forecast_upper = load_model(FORECAST_N2_UPPER_PATH)
    else:
        forecast_model = load_model(FORECAST_MODEL_PATH)
        forecast_lower = load_model(FORECAST_LOWER_PATH)
        forecast_upper = load_model(FORECAST_UPPER_PATH)

    if risk_model is None or forecast_model is None:
        raise RuntimeError(
            f"Models not found for horizon={horizon}. "
            f"Run `python manage.py train_models` first."
        )

    X_full, _, _, meta = build_feature_matrix()
    latest_per_ward = meta.loc[meta.groupby("ward_name")["year"].idxmax()].copy()

    label_map_rev = {0: "Low", 1: "Medium", 2: "High"}
    results = []

    for _, row in latest_per_ward.iterrows():
        ward_name = row["ward_name"]

        ward_features = X_full.loc[
            (X_full.index == meta.index) & (meta["ward_name"] == ward_name)
        ]
        if ward_features.empty:
            continue

        X_pred = ward_features.iloc[-1:].copy()
        X_pred_scaled = scale_features(X_pred)

        risk_idx = risk_model.predict(X_pred_scaled)[0]
        predicted_risk = label_map_rev.get(int(risk_idx), "Medium")

        predicted_complaints = int(round(forecast_model.predict(X_pred_scaled)[0]))
        pred_lower = int(round(forecast_lower.predict(X_pred_scaled)[0]))
        pred_upper = int(round(forecast_upper.predict(X_pred_scaled)[0]))
        health_score = row.get("health_score", None)

        recommendation = generate_recommendation(
            predicted_risk, predicted_complaints, health_score, ward_name,
        )

        from ml.utils import load_model as lm
        expected_cols = lm(FEATURES_PATH)
        top_feats = _top_features(X_pred, expected_cols)

        results.append({
            "ward_name": ward_name,
            "predicted_risk": predicted_risk,
            "predicted_complaints": max(0, predicted_complaints),
            "predicted_complaints_lower": max(0, min(pred_lower, predicted_complaints)),
            "predicted_complaints_upper": max(pred_upper, predicted_complaints),
            "predicted_health_score": health_score,
            "recommendation": recommendation,
            "top_features": top_feats,
        })

    return results, target_year
