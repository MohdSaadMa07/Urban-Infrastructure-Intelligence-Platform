"""
Celery tasks for UrbanIQ Phase 2.

Scheduled nightly:
  1. generate_predictions  - run predictions for all wards, save to DB
  2. retrain_models        - (optional) retrain on latest data
"""

from celery import shared_task
from datetime import date


@shared_task
def generate_predictions():
    """
    Generate predictions for all wards and save to WardPrediction table.
    Runs nightly via Celery Beat.
    """
    from ml.predict import generate_predictions as run_prediction
    from ml.utils import load_model, RISK_MODEL_PATH
    from api.models import WardPrediction, Ward
    from api.serializers import WardPredictionSerializer

    # Check if models exist
    if not RISK_MODEL_PATH.exists():
        return {"status": "error", "message": "Models not found. Run train_models first."}

    results, target_year = run_prediction()
    if not results:
        return {"status": "error", "message": "No predictions generated."}

    created = 0
    for r in results:
        ward = Ward.objects.filter(ward_name=r["ward_name"]).first()
        if not ward:
            continue
        WardPrediction.objects.create(
            ward=ward,
            prediction_date=date.today(),
            predicted_risk=r["predicted_risk"].lower(),
            predicted_complaints=r["predicted_complaints"],
            predicted_health_score=r["predicted_health_score"],
            recommendation=r["recommendation"],
            model_version=f"xgboost-v1-{target_year}",
        )
        created += 1

    return {
        "status": "success",
        "wards_updated": created,
        "target_year": target_year,
    }


@shared_task
def retrain_models():
    """
    Retrain all ML models on latest CivicMetrics data.
    """
    from ml.features import build_feature_matrix
    from ml.train import train_risk_model, train_forecast_model, train_clustering

    X, y_risk, y_complaints, _ = build_feature_matrix()
    train_risk_model(X, y_risk)
    train_forecast_model(X, y_complaints)
    train_clustering(X)
    return {"status": "success", "rows": len(X)}
