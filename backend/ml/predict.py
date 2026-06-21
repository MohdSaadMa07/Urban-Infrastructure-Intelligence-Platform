"""
Prediction generation for all wards.

Loads trained models and generates:
  - Risk classification
  - Complaint forecast (with prediction intervals)
  - DBSCAN cluster assignment
  - Health score
  - Recommendation
  - Per-ward top contributing features

Supports multi-year iterative prediction.
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
    CLUSTER_MODEL_PATH,
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


def _predict_from_features(X_pred, risk_model, forecast_model,
                           forecast_lower, forecast_upper,
                           row, ward_name, cluster_data):
    """Run prediction on a feature vector and return result dict with intervals."""
    label_map_rev = {0: "Low", 1: "Medium", 2: "High"}
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

    # Per-ward top features
    from ml.utils import load_model as lm
    expected_cols = lm(FEATURES_PATH)
    top_feats = _top_features(X_pred, expected_cols)

    return {
        "ward_name": ward_name,
        "predicted_risk": predicted_risk,
        "predicted_complaints": max(0, predicted_complaints),
        "predicted_complaints_lower": max(0, min(pred_lower, predicted_complaints)),
        "predicted_complaints_upper": max(pred_upper, predicted_complaints),
        "predicted_health_score": health_score,
        "recommendation": recommendation,
        "top_features": top_feats,
    }


def _build_feature_row(ward_name, year, latest_meta_row, predicted_complaints):
    prev_total = latest_meta_row.get("total_complaints", 0)
    growth_rate = ((predicted_complaints - prev_total) / max(prev_total, 1)) * 100

    return {
        "ward_name": ward_name,
        "year": year,
        "total_complaints": predicted_complaints,
        "health_score": latest_meta_row.get("health_score", 50),
        "complaint_growth_rate": growth_rate,
    }


def generate_predictions(target_year=None, previous_predictions=None):
    """
    Generate predictions for all wards for a target year.
    Returns point predictions, intervals, risk, recommendation, and top features.
    """
    from api.models import Ward

    if target_year is None:
        from api.models import CivicMetrics
        latest = CivicMetrics.objects.order_by("-year").values_list("year", flat=True).first()
        target_year = (latest or 2026) + 1

    # Load all models
    risk_model = load_model(RISK_MODEL_PATH)
    forecast_model = load_model(FORECAST_MODEL_PATH)
    forecast_lower = load_model(FORECAST_LOWER_PATH)
    forecast_upper = load_model(FORECAST_UPPER_PATH)
    cluster_data = load_model(CLUSTER_MODEL_PATH)

    if risk_model is None or forecast_model is None:
        raise RuntimeError("Models not found. Run `python manage.py train_models` first.")

    X_full, _, _, meta = build_feature_matrix()

    if previous_predictions:
        # Iterative multi-year prediction
        prev_by_ward = {p["ward_name"]: p for p in previous_predictions}
        latest_idx = meta.groupby("ward_name")["year"].idxmax()
        latest_meta = meta.loc[latest_idx].copy()

        results = []
        for _, row in latest_meta.iterrows():
            ward_name = row["ward_name"]
            if ward_name not in prev_by_ward:
                continue

            ward_features = X_full.loc[
                (X_full.index == meta.index) & (meta["ward_name"] == ward_name)
            ]
            if ward_features.empty:
                continue

            X_pred = ward_features.iloc[-1:].copy()
            prev_p = prev_by_ward[ward_name]

            actual_complaints = row.get("total_complaints", 0)
            if actual_complaints > 0:
                predicted_growth = (
                    (prev_p["predicted_complaints"] - actual_complaints)
                    / actual_complaints * 100
                )
                if "complaint_growth_rate" in X_pred.columns:
                    X_pred["complaint_growth_rate"] = predicted_growth

            result = _predict_from_features(
                X_pred, risk_model, forecast_model,
                forecast_lower, forecast_upper,
                row, ward_name, cluster_data,
            )
            results.append(result)
        return results, target_year

    # Standard single-year prediction
    latest_per_ward = meta.loc[meta.groupby("ward_name")["year"].idxmax()].copy()

    results = []
    for _, row in latest_per_ward.iterrows():
        ward_name = row["ward_name"]

        ward_features = X_full.loc[
            (X_full.index == meta.index) & (meta["ward_name"] == ward_name)
        ]
        if ward_features.empty:
            continue

        X_pred = ward_features.iloc[-1:].copy()
        result = _predict_from_features(
            X_pred, risk_model, forecast_model,
            forecast_lower, forecast_upper,
            row, ward_name, cluster_data,
        )
        results.append(result)

    return results, target_year
