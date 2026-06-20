"""
Prediction generation for all wards.

Loads trained models and generates:
  - Risk classification
  - Complaint forecast
  - DBSCAN cluster assignment
  - Health score
  - Recommendation
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
    CLUSTER_MODEL_PATH,
    SCALER_PATH,
    FEATURES_PATH,
)


def generate_predictions(target_year=None):
    """
    Generate predictions for all wards for a target year.

    Args:
        target_year: int year to predict for (default: latest year + 1)

    Returns:
        list of dicts ready for WardPrediction model bulk create
    """
    from api.models import Ward

    if target_year is None:
        # Default to latest year + 1
        from api.models import CivicMetrics
        latest = CivicMetrics.objects.order_by("-year").values_list("year", flat=True).first()
        target_year = (latest or 2026) + 1

    # Load models
    risk_model = load_model(RISK_MODEL_PATH)
    forecast_model = load_model(FORECAST_MODEL_PATH)
    cluster_data = load_model(CLUSTER_MODEL_PATH)
    scaler = load_model(SCALER_PATH)
    feature_cols = load_model(FEATURES_PATH)

    if risk_model is None or forecast_model is None:
        raise RuntimeError(
            "Models not found. Run `python manage.py train_models` first."
        )

    # Build feature matrix for all available years (needed for lagged features)
    X_full, _, _, meta = build_feature_matrix()

    # Filter to latest year per ward as the base for prediction
    # We need to construct feature vectors for the target_year
    latest_per_ward = meta.loc[meta.groupby("ward_name")["year"].idxmax()].copy()

    results = []
    for _, row in latest_per_ward.iterrows():
        ward_name = row["ward_name"]

        # Get the feature vector for this ward's latest year
        ward_features = X_full.loc[
            (X_full.index == meta.index) & (meta["ward_name"] == ward_name)
        ]

        if ward_features.empty:
            # Fallback: use latest year for any ward
            continue

        # For now, use the latest known feature vector as the prediction input
        # In a more advanced setup, we'd project features forward
        X_pred = ward_features.iloc[-1:].copy()

        # Scale
        X_pred_scaled = scale_features(X_pred)

        # Predict risk
        label_map_rev = {0: "Low", 1: "Medium", 2: "High"}
        risk_idx = risk_model.predict(X_pred_scaled)[0]
        predicted_risk = label_map_rev.get(int(risk_idx), "Medium")

        # Predict complaints
        predicted_complaints = int(round(forecast_model.predict(X_pred_scaled)[0]))

        # Health score from latest metrics
        health_score = row.get("health_score", None)

        # Recommendation
        recommendation = generate_recommendation(
            predicted_risk,
            predicted_complaints,
            health_score,
            ward_name,
        )

        # DBSCAN cluster assignment
        cluster_label = -1
        if cluster_data:
            # Re-fit DBSCAN on full data + this prediction point
            # For simplicity, use the saved cluster assignment or None
            cluster_label = cluster_data.get("labels", [-1])[0]

        results.append({
            "ward_name": ward_name,
            "predicted_risk": predicted_risk,
            "predicted_complaints": max(0, predicted_complaints),
            "predicted_health_score": health_score,
            "recommendation": recommendation,
            "cluster_label": int(cluster_label),
        })

    return results, target_year
